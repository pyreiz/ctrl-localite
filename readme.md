 [![MIT license](https://img.shields.io/badge/License-MIT-blue.svg)](https://en.wikipedia.org/wiki/MIT_License) [![pytest-status](https://github.com/pyreiz/ctrl-localite/workflows/pytest/badge.svg)](https://github.com/pyreiz/ctrl-localite/actions) [![Coverage Status](https://coveralls.io/repos/github/pyreiz/ctrl-localite/badge.svg?branch=develop)](https://coveralls.io/github/pyreiz/ctrl-localite?branch=develop)

### ctrl-localite

A repository to control localite 4.0 

### Command Line Tools

- localiteLSL

starts reading from localite TCP/IP-json and forwards all stimulation trigger
events as LSL Marker stream

- localiteMock

mocks a localite TCP/IP-json server for testing and development


### Information Flow

![Alt text](https://g.gravizo.com/source/custom_mark10?https://raw.githubusercontent.com/pyreiz/ctrl-localite/develop/readme.md)
<details> 
<summary></summary>
custom_mark10
    digraph Flow { 
        rankdir=LR;     
        {
        node [shape = circle]
        node [style=filled]
        rankdir=LR;            
        QUEUE -> CTRL
        EXT -> QUEUE        
        CTRL -> LOC
        CTRL -> MRK
        LOC -> QUEUE   
        }
        fo[label="", shape=plaintext] 
        fo -> EXT
        to[label="", shape=plaintext] 
        lo[label="", shape=plaintext] 
        MRK -> to
        LOC -> lo
    }
custom_mark10
</details>

The EXT receives a payload via JSON over TCP-IP. Payloads have to have the form
`[<fmt>:str, <message>:str, <tstamp>:int]`. The fmt defines how the message will be distributed. Only the following targets for `fmt` are valid: `["cmd", "mrk", "loc"]`. Invalid fmts will not be forwarded, and their message ignored. 

Whether the message part of the payload is valid depends on the recipient and will be evaluated there.

