#! python3

import atexit
import json
from queue import Queue
import sys
from threading import Thread, Event, Lock
from subprocess import Popen, PIPE
from os import path, environ

NODE_EXECUTABLE = path.join(path.dirname(__file__), "node")
VM_SERVER = path.join(path.dirname(__file__), "vm-server")

PY35 = 0x03050000 <= sys.hexversion < 0x03060000
if PY35:
    NODE_EXECUTABLE = path.join(path.dirname(__file__), "node_xp")
    VM_SERVER = path.join(path.dirname(__file__), "vm-server_xp")


def eval(code, **options):
    """A shortcut to eval JavaScript.

    :param str code: The code to be run.
    :param options: Additional options sent to :meth:`VM.__init__`.

    This function will create a :class:`VM`, run the code, and return the
    result.
    """
    with VM(**options) as vm:
        return vm.run(code)


DEFAULT_BRIDGE = None


def default_bridge():
    global DEFAULT_BRIDGE
    if DEFAULT_BRIDGE is not None:
        return DEFAULT_BRIDGE

    DEFAULT_BRIDGE = VMServer().start()
    return DEFAULT_BRIDGE


@atexit.register
def close():
    if DEFAULT_BRIDGE is not None:
        DEFAULT_BRIDGE.close()


class BaseVM:
    """BaseVM class, containing some common methods for VMs.
    """

    def __init__(self, server=None):
        """
        :param VMServer server: Optional. If provided, the VM will be created
            on the server. Otherwise, the VM will be created on a default
            server, which is started on the first creation of VMs.
        """
        if server is None:
            server = default_bridge()
        self.bridge = server
        self.id = None
        self.event_que = None
        self.console = "off"

    def __enter__(self):
        """This class can be used as a context manager, which automatically
        :meth:`create` when entering the context.
        """
        self.create()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """See :meth:`destroy`"""
        self.destroy()

    def before_create(self, data):
        """Overwrite. Extend data before creating the VM."""
        pass

    def create(self):
        """Create the VM."""
        data = {"action": "create"}
        self.before_create(data)
        self.id = self.communicate(data)
        self.bridge.add_vm(self)
        return self

    def destroy(self):
        """Destroy the VM."""
        self.communicate({"action": "destroy"})
        self.bridge.remove_vm(self)
        self.id = None
        return self

    def communicate(self, data):
        """Communicate with server. Wraps :meth:`VMServer.communicate` so we
        can add additional properties to data.

        This method would raise an :class:`VMError` if vm-server response an
        error.
        """
        data["vmId"] = self.id
        data = self.bridge.communicate(data)
        if data["status"] != "success":
            raise VMError(data["error"])
        return data.get("value")


class VM(BaseVM):
    """VM class, represent `vm2.VM <https://github.com/patriksimek/vm2#vm>`_.
    """

    def __init__(self, code=None, server=None, **options):
        """
        :param str code: Optional JavaScript code to run after creating
            the VM. Useful to define some functions.

        :param VMServer server: Optional VMServer. See :class:`BaseVM`
            for details.

        :param options: The options for `vm2.VM`_.
        """
        super().__init__(server)
        self.id = None
        self.code = code
        self.options = options

    def before_create(self, data):
        """Create VM."""
        data.update(type="VM", code=self.code, options=self.options)

    def run(self, code):
        """Execute JavaScript and return the result.

        If the server responses an error, a :class:`VMError` will be raised.
        """
        return self.communicate({"action": "run", "code": code})

    def call(self, function_name, *args):
        """Call a function and return the result.

        :param str function_name: The function to call.
        :param args: Function arguments.

        function_name can include "." to call functions on an object. However,
        it is called like:

        .. code-block:: javascript

            var func = vm.run("function.to.call");
            return func(...args);

        So ``this`` keyword might doesn't work as expected.
        """
        return self.communicate({
            "action": "call",
            "functionName": function_name,
            "args": args
        })


class NodeVM(BaseVM):
    """NodeVM class, represent `vm2.NodeVM
    <https://github.com/patriksimek/vm2#nodevm>`_.
    """

    def __init__(self, server=None, **options):
        """
        :param VMServer server: Optional VMServer. See :class:`BaseVM`
            for details.

        :param options: the options for `vm2.NodeVM`_.

        If ``console="redirect"``, those console output will return as events,
        stored in an event queue, which could be accessed with
        :attr:`event_que`.
        """
        super().__init__(server)
        self.options = options
        self.console = options.get("console", "inherit")

        self.event_que = Queue()
        """A :class:`queue.Queue` object containing console events.

        An event is a :class:`dict` and you can get the text value with:

        .. code:: python

            event = self.event_que.get()
            text = event.get("value")

        """

    def before_create(self, data):
        """Create NodeVM."""
        data.update(type="NodeVM", options=self.options)

    def run(self, code, filename=None):
        """Run the code and return a :class:`NodeVMModule`.

        :param str code: The code to be run. The code should look like a
            commonjs module (or an IIFE module, according to the options). See
            `vm2.NodeVM`_ for details.

        :param str filename: Optional, used for stack trace. Currently this
            has no effect. (should vm-server send traceback back?)

        :return: :class:`NodeVMModule`.
        """
        id = self.communicate({
            "action": "run",
            "code": code,
            "filename": filename
        })
        return NodeVMModule(id, self)

    @classmethod
    def code(cls, code, filename=None, **kwargs):
        """A class method helping you create a module in VM.

        :param str code: The code sent to :meth:`run`.
        :param str filename: The filename sent to :meth:`run`.
        :param kwargs: Other arguments are sent to constructor.

        .. code-block:: python

            with NodeVM() as vm:
                module = vm.run(code)
                result = module.call_member("method")

        vs.

        .. code-block:: python

            with NodeVM.code(code) as module:
                result = module.call_member("method")
                # access the vm with `module.vm`
        """
        vm = cls(**kwargs)
        module = vm.create().run(code, filename)
        module.CLOSE_ON_EXIT = True
        return module


class NodeVMModule:
    """Since we can only pass JSON between python and node, we use
    this wrapper to access the module created by :meth:`NodeVM.run`.

    This class shouldn't be initiated by users directly.

    You can access the VM object with attribute :attr:`NodeVMModule.vm`.
    """

    def __init__(self, id, vm):
        self.id = id
        self.vm = vm
        self.CLOSE_ON_EXIT = False

    def __enter__(self):
        """This class can be used as a context manager. See :meth:`NodeVM.code`.
        """
        return self

    def __exit__(self, exc_type, exc_value, tracback):
        """Destroy the VM if:

        1. This method is called.
        2. The module is created by :meth:`NodeVM.code`.
        """
        if self.CLOSE_ON_EXIT:
            self.vm.destroy()

    def communicate(self, data):
        """Wraps :meth:`vm.communicate`. So we can set additional properties
        on the data before communication.
        """
        data["moduleId"] = self.id
        return self.vm.communicate(data)

    def call(self, *args):
        """Call the module, in case that the module itself is a function."""
        return self.communicate({
            "action": "call",
            "args": args
        })

    def get(self):
        """Return the module, in case that the module itself is json-encodable.
        """
        return self.communicate({
            "action": "get"
        })

    def call_member(self, member, *args):
        """Call a function member.

        :param str member: Member's name.
        :param args: Function arguments.
        """
        return self.communicate({
            "action": "callMember",
            "member": member,
            "args": args
        })

    def get_member(self, member):
        """Return member value.

        :param str member: Member's name.
        """
        return self.communicate({
            "action": "getMember",
            "member": member
        })

    def destroy(self):
        """Destroy the module.

        You don't need this if you can just destroy the VM.
        """
        out = self.communicate({
            "action": "destroyModule"
        })
        if self.CLOSE_ON_EXIT:
            self.vm.destroy()
        return out


class VMServer:
    """VMServer class, represent vm-server. See :meth:`start` for details."""

    def __init__(self, command=None):
        """
        :param str command: the command to spawn node process. If not set, it
            would use:

            1. Environment variable ``NODE_EXECUTABLE``
            2. "node"
        """

        self.closed = None
        self.process = None
        self.vms = {}
        self.poll = {}
        self.write_lock = Lock()
        self.poll_lock = Lock()
        self.inc = 1
        if command is None:
            command = environ.get("NODE_EXECUTABLE", NODE_EXECUTABLE)
        self.command = command

    def __enter__(self):
        """This class can be used as a context manager, which automatically
        :meth:`start` the server.

        .. code-block:: python

            server = VMServer()
            server.start()
            # create VMs on the server...
            server.close()

        vs.

        .. code-block:: python

            with VMServer() as server:
                # create VMs on the server...
        """
        return self.start()

    def __exit__(self, exc_type, exc_value, traceback):
        """See :meth:`close`."""
        self.close()

    def start(self):
        """Spawn a Node.js subprocess and run vm-server.F

        vm-server is a REPL server, which allows us to connect to it with
        stdios. You can find the script at ``node_vm2/vm-server`` (`Github
        <https://github.com/eight04/node_vm2/tree/master/node_vm2/vm-server>`__).

        There are 2 ways to specify ``node`` executable:
            1. Add the directory of ``node`` to ``PATH`` env variable.
            2. Set env variable ``NODE_EXECUTABLE`` to the path of the executable.

        Communication using JSON::

            > {"id": 1, "action": "create", "type": "VM"}
            {"id": 1, "status": "success"}

            > {"id": 2, "action": "run", "code": "var a = 0; a += 10; a"}
            {"id": 2, "status": "success", "value": 10}

            > {"id": 3, "action": "xxx"}
            {"id": 3, "status": "error", "error": "Unknown action: xxx"}
        """
        if self.closed:
            raise VMError("The VM is closed")

        args = [self.command, "--harmony", VM_SERVER]
        self.process = Popen(args, bufsize=0, stdin=PIPE, stdout=PIPE)

        def reader():
            for data in self.process.stdout:
                try:
                    # FIXME: https://github.com/PyCQA/pylint/issues/922
                    data = json.loads(data.decode("utf-8")) or {}
                except json.JSONDecodeError:
                    # the server is down?
                    self.close()
                    return

                if data["type"] == "response":
                    with self.poll_lock:
                        self.poll[data["id"]][1] = data
                        self.poll[data["id"]][0].set()

                elif data["type"] == "event":
                    try:
                        vm = self.vms[data["vmId"]]
                    except KeyError:
                        # the vm is destroyed
                        continue

                    if data["name"] == "console.log":
                        if vm.console == "redirect":
                            vm.event_que.put(data)

                        elif vm.console == "inherit":
                            sys.stdout.write(data.get("value", "") + "\n")

                    elif data["name"] == "console.error":
                        if vm.console == "redirect":
                            vm.event_que.put(data)

                        elif vm.console == "inherit":
                            sys.stderr.write(data.get("value", "") + "\n")

        Thread(target=reader, daemon=True).start()

        data = self.communicate({"action": "ping"})
        if data["status"] == "error":
            raise VMError("Failed to start: " + data["error"])
        self.closed = False
        return self

    def close(self):
        """Close the server. Once the server is closed, it can't be
        re-open."""
        if self.closed:
            return self
        try:
            data = self.communicate({"action": "close"})
            if data["status"] == "error":
                raise VMError("Failed to close: " + data["error"])
        except OSError:
            # the process is down?
            pass
        self.process.communicate()
        self.process = None
        self.closed = True

        with self.poll_lock:
            for event, _data in self.poll.values():
                event.set()
        return self

    def add_vm(self, vm):
        self.vms[vm.id] = vm

    def remove_vm(self, vm):
        del self.vms[vm.id]

    def generate_id(self):
        """Generate unique id for each communication."""
        inc = self.inc
        self.inc += 1
        return inc

    def communicate(self, data):
        """Send data to Node and return the response.

        :param dict data: must be json-encodable and follow vm-server's
            protocol. An unique id is automatically assigned to data.

        This method is thread-safe.
        """
        id = self.generate_id()

        data["id"] = id
        text = json.dumps(data) + "\n"

        event = Event()

        with self.poll_lock:
            self.poll[id] = [event, None]

        # FIXME: do we really need lock for write?
        with self.write_lock:
            self.process.stdin.write(text.encode("utf-8"))

        event.wait()

        with self.poll_lock:
            data = self.poll[id][1]
            del self.poll[id]
        return data


class VMError(Exception):
    """Errors thrown by VM."""
    pass