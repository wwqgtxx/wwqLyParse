# 下载网址解析

## 函数原型
```
def ParseURL(url, label, min=None, max=None)
```
* **参数**
    * url 单行文本，解析时使用的内容
    * label 单行文本，Parse 函数返回结果中 code 或 label 值
    * min 整数 或 None, 希望获取的 分段文件信息的 最小 序号, 按数组下标, 0 表示第 1 段。为 None 表示最小值，即 0
    * max 整数 或 None，希望获取的 分段文件信息的 最大 序号, 按数组下标, 0 表示第 1 段。为 None 表示最大值，即不限制
* **返回结果** 视频信息(dict) 的列表

下载解析用来返回需要下载的实际网址，具体格式如下：
```
[
    {
        "protocol" : "http", 
        "urls" : [""],
        "args" : {},
        "proxy" : {},
        "duration" : 1111,
        "length" : 222222,
        "decrypt" : "KanKan",
        "decryptData" : {},
        "adjust" : "KanKan", 
        "adjustData" : { },
        "segmentSize": 1024,
        "maxDown" : 5,
        "convert" : "",
        "convertData" : "",
    }
    ......
]
```
整体是一个 数组 ( list , [] , Array ), 数组的每一项是一个 dict ( {} , Object )。每个 dict 表示一个要下载内容的下载信息，一般来讲，对应于分段视频中的一个分段，具体定义有： 
* protocol ： 单行文本 下载使用的协议，目前支持：
    * http
    * proxy-http : 支持通过代理访问的 http 
    * https : 支持代理
    * m3u8 : 传输使用协议为 http
    * hds : 按文件为 f4m 列表进行处理
* urls : 单行字符串 或字符串数组，用于表示下载地址列表，是指同一段视频的不同下载网址。在 protocol 为 m3u8 时可以指定为本地文件，这时使用文件路径的全路径表示，即 file:///C:\file.m3u8 
* args : 可选 类型：dict, object, 下载协议所需要的额外信息
    * 对于http 协议，args 是额外的 http 头,如 User-Agent , Referer 等，如果不需要，可为 {}，或不指定该项
* proxy : 可选 类型：dict, object，下载是使用的代理信息，具体属性有：
    * type : 代理类型，可能值有 http, http 1.0, socks4, socks5, socks4a, socks5h
    * host : 代理服务器名称，为域名或IP地址
    * port : 代理端口 
    * auth : 验证类型，默认为不需要验证，可能值有 none, basic, digest,negotiate, gssnegotiate, ntlm, digest_ie,ntlm_wb, only, any, anySafe。这些值可同时设置，中间使用 , 来分隔
    * user : 用户名
    * pwd ：密码
* duration :  可选 类型：整数，表示该段视频的播放时长，单位毫秒
* length : 可选 整数，表示该段视频的总字节数
* decrypt : 可选 单行文件，用于在下载完成后对数据进行解密，对于 Python 插件，该字段为进行调整的函数名；对于 C# 插件，则需要实现IDecryptDown 接口，该值 和 decryptData、以及下载的文件路径为调用参数
* decryptData : 可选 类型：dict( {}, object )，调用 decrypt 会转换成Json传入（如果是字符串则不转换）
* adjust : 可选，类型：字符串，该值一般与 adjustData 成对出现，用于对网址做下载地址二次分析。该字符串是二次处理代码名称，对于 Python 插件，该字段为进行调整的函数名；对于 C# 插件，则需要实现 IAdjustDown 接口，该值和 adjustData 分别为调用 Adjust 方法时的同个参数。
* adjustData : 可选，类型：dict( {}, object )，在调用 adjust 时用作参数

另外，还可以指定下载的一些整体信息，对于多段情况，该项信息只需要在其中一条指定即可，以最后一条指定的值为准 
* unfixIp : 表示网址是可以在各IP地址间切换，可尝试从其他服务器上下载
* segmentSize : 指定分片下载的每片大小，指定该表示使用分片下载方式
* maxDown: 最大并发下载数量
* convert 可选，类型：单行文本，用于指定下载完成后进行下载文件转换的方法，该字符串指定转换代码的名称，对于 Python 插件，该字段为进行调整的函数名；对于 C# 插件，则需要实现 IConvertDown 接口，该值和 convertData 分别为调用 Convert 方法的参数
* convertData 可选，类型：dict( {}, object)，在调用 convert 时用作参数

***

* m3u8 : 对于 m3u8 协议，主要是给的网址对于一个 m3u8 文件，这时下载程序将把 m3u8 文件下载后，将之展开并下载列表中的实际视频文件。对于 master playlist ，在 protocol后面添加 使用 | 分隔的选择信息，两者使用 ： 隔开。如 m3u8:VideoLabel|VideoLabel
* hds : 对于 hds 协议(扩展名一般为 f4m)，主要是给的网址对于一个 m3u8 文件，这时下载程序将把 m3u8 文件下载后，将之展开并下载列表中的实际视频文件。对于 master playlist ，在 protocol后面添加 : 后可指定进一步的过滤条件，如 hds:@bitrate='5000'
