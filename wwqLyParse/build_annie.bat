cd %~dp0/annie/
SET GOPATH="%~dp0/annie"
SET GOARCH=386
go build -o annie32.exe src/github.com/iawia002/annie/main.go
SET GOARCH=amd64
go build -o annie64.exe src/github.com/iawia002/annie/main.go
cd %~dp0
@pause