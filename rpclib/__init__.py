#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
    RPC_CALL = 1
    RPC_VERSION = 2

    MY_PROGRAM_ID = 1234 # assigned by Sun
    MY_VERSION_ID = 1000
    MY_TIME_PROCEDURE_ID = 9999

    AUTH_NULL = 0
    CALL = 0
    # send an Sun RPC call package
    p.pack_uint(transaction)
    p.pack_enum(RPC_CALL)
    p.pack_uint(RPC_VERSION)
    p.pack_uint(MY_PROGRAM_ID)
    p.pack_uint(MY_VERSION_ID)
    p.pack_uint(MY_TIME_PROCEDURE_ID)
    p.pack_enum(AUTH_NULL)
    p.pack_uint(0)
    p.pack_enum(AUTH_NULL)
    p.pack_uint(0)"""

__author__ = 'jershell'
import socket
import xdrlib
import struct
AUTH_NULL = 0

def ip2int(addr):
    return struct.unpack("!I", socket.inet_aton(addr))[0]

def int2ip(addr):
    return socket.inet_ntoa(struct.pack("!I", addr))

def bit_count(int_type):
    count = 0
    while int_type:
        int_type &= int_type - 1
        count += 1
    return count

def auth(pack, auth):
    flavor, stuff = auth
    pack.pack_enum(flavor)
    pack.pack_opaque(stuff)

def unpack_auth(unpack):
    flavor = unpack.unpack_enum()
    stuff = unpack.unpack_opaque()
    return (flavor, stuff)

def make_auth_null():
    return b''

def getExportList(host, port, timeout=1):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((host, port))
    client.settimeout(timeout)
    e_pack = xdrlib.Packer()
    e_pack.pack_uint(0x80000028)
    e_pack.pack_uint(0x525b8117)
    e_pack.pack_enum(0)
    e_pack.pack_uint(2)
    e_pack.pack_uint(100005)
    e_pack.pack_uint(3)
    e_pack.pack_uint(5)
    #cred verif
    e_cred = (AUTH_NULL, make_auth_null())
    e_verf = (AUTH_NULL, make_auth_null())
    auth(e_pack, e_cred)
    auth(e_pack, e_verf)
    e_data = e_pack.get_buffer()
    client.send(e_data)
    try:
        export_rev = client.recv(2048)
    except:
        return False
    finally:
        client.close()
    e_u = xdrlib.Unpacker(export_rev)
    e_header = e_u.unpack_uint()
    e_xid = e_u.unpack_uint()
    e_msg_reply = e_u.unpack_uint()
    e_reply_state = e_u.unpack_uint()
    e_verf_flavor = e_u.unpack_uint()
    e_verf_len = e_u.unpack_uint()
    e_accept_state = e_u.unpack_uint()

    #export structures
    export_list = {
        "host": host,
        "port": port,
        "structures": [],
    }

    next_value = e_u.unpack_uint()
    while next_value:
        value_dir = e_u.unpack_string()
        groups = e_u.unpack_uint()
        groups_array = []
        while groups:
            group = e_u.unpack_string()
            groups_array.append(group)
            groups = e_u.unpack_uint()
        export_list["structures"].append(
            {
                "dir": value_dir,
                "groups": groups_array,
            }
        )
        next_value = e_u.unpack_uint()
    """print(
        " e_header", e_header, "\n",
        "e_xid", e_xid, "\n",
        "e_msg_reply", e_msg_reply, "\n",
        "e_reply_state", e_reply_state, "\n",
        "e_verf_flavor", e_verf_flavor, "\n",
        "e_verf_len", e_verf_len, "\n",
        "e_accept_state", e_accept_state, "\n",
        "structures", structures, "\n",
    )"""
    return export_list

def getPort(host, prog, timeout):
    TID = 0x525b8116
    TYPE = 0
    RPCVERSION = 2
    CALL = 0
    PROGRAMM = 100000
    PROGRAMMVERSION = 2
    PROCEDURE = 3  #GETPORT(3)

    port = 111
#    host = '100.64.0.65'
    size = 2048
#
    ##Call Mount
#    CPROGRAMM = 100005 #MOUNT
    CPROGRAMM = prog
    CVERSION = 3
    CPROTO = 6
    CPORT = 0

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.connect((host, port))
    client_socket.settimeout(timeout)
    p = xdrlib.Packer()

    p.pack_uint(TID)
    p.pack_enum(TYPE)
    p.pack_uint(RPCVERSION)
    p.pack_uint(PROGRAMM)
    p.pack_uint(PROGRAMMVERSION)
    p.pack_uint(PROCEDURE)
    cred = (AUTH_NULL, make_auth_null())
    verf = (AUTH_NULL, make_auth_null())
    auth(p, cred)
    auth(p, verf)
    #
    p.pack_uint(CPROGRAMM)
    p.pack_uint(CVERSION)
    p.pack_uint(CPROTO)
    p.pack_uint(CPORT)
    #
    data = p.get_buffer()
    client_socket.send(data)
    export_list = True
    try:
        rev_data = client_socket.recv(size)
        u = xdrlib.Unpacker(rev_data)
        xid = u.unpack_uint()
        msg_type = u.unpack_uint()
        reply_state = u.unpack_uint()
        flavor = u.unpack_uint()
        length = u.unpack_uint()
        a_state = u.unpack_uint()
        #verifier = unpack_auth(u)
        r_port = u.unpack_uint()
        #value = u.unpack_uint()
        #print(" xid:", xid, "\n",
        #    "msg_type:", msg_type, "\n",
        #    "reply_state:", reply_state, "\n",
        #    "flavor:", flavor, "\n",
        #    "length:", length, "\n",
        #    "a_state:", a_state, "\n",
        #    #"verifier:", verifier, "\n",
        #    "r_port:", r_port, "\n",)
        #    "value:", value, "\n")
        return r_port
    except:
        return False
    finally:
        client_socket.close()

def check_host(host):
    port = getPort(host, 100005, 3)  # 100005 - MOUNT
    if port:
        exportList = getExportList(host, port, 3)
        if exportList:
            return True
    else:
        return False





