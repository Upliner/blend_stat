#!/usr/bin/python3

import os, sys, struct

bstruct = struct.Struct("<4sIQII")

verbose = False

def read_str_arr(name, data):
    if data[:4] != name:
       raise Exception("Invalid SDNA")
    data = data[4:]
    cnt, = struct.unpack("<I", data[:4])
    data = data[4:]
    result = data.split(b"\0")[:cnt]
    return result, data[sum(len(name)+1 for name in result)+3&~3:]

def read_sdna(data):
    if data[:4] != b"SDNA":
       raise Exception("Invalid SDNA")
    data = data[4:]
    names, data = read_str_arr(b"NAME",data)
    types, data = read_str_arr(b"TYPE",data)
    if data[:4] != b"TLEN":
       raise Exception("Invalid SDNA")
    data = data[4+len(types)*2+3&~3:]
    if data[:4] != b"STRC":
       raise Exception("Invalid SDNA", data[:4])
    data = data[4:]
    cnt, = struct.unpack("<I", data[:4])
    data = data[4:]
    result = []
    for i in range(cnt):
        typ, field_cnt = struct.unpack("<HH", data[:4])
        result.append(types[typ].decode("ascii"))
        data = data[4+4*field_cnt:]
    return result

def stat_file(f):
    magic = f.read(9)
    if magic != b"BLENDER-v":
        print("Incompatible blend file")
        print(magic)
        quit(1)
    version = f.read(3).decode("ascii")
    print(f"Blender version {version[0]}.{int(version[1:])}")
    blocks = []
    while True:
        bhdr = f.read(bstruct.size)
        if len(bhdr) != bstruct.size:
            print("Unexpected end of file")
            break
        block = bstruct.unpack(bhdr)
        blocks.append(block)
        btype = block[0]
        size = block[1]
        if btype == b"ENDB":
            break
        if btype == b"DNA1":
            sdna = read_sdna(f.read(size))
        else:
            f.seek(size, os.SEEK_CUR)

    stats_sdna = {}
    stats_blk = {}
    typ = sdna[0]
    btyp = ""
    for btype, size, addr, sdna_index, cnt in blocks:
        if sdna_index > 0:
            typ = sdna[sdna_index]
        elif btype != b"DATA":
            typ = btype.strip(b'\0').decode("ascii")
        stat_item = stats_sdna.get(typ, [0, 0, 0])
        stat_item[0] += size+bstruct.size
        stat_item[1] += cnt
        stat_item[2] += 1
        stats_sdna[typ] = stat_item

        btype = btype.strip(b'\0').decode("ascii")
        if btype != "DATA":
            btyp = btype
        stat_item = stats_blk.get(btyp, [0, 0, 0])
        stat_item[0] += size+bstruct.size
        stat_item[1] += 1
        if btype != "DATA":
            stat_item[2] += 1
        stats_blk[btyp] = stat_item

        if verbose:
            print(btype, "size="+str(size),"addr="+hex(addr),"sdna="+str(sdna_index), "type="+typ, "cnt="+str(cnt))

    print()
    stats = list(stats_sdna.items())
    stats.sort(key=lambda a: a[1], reverse=True)
    for typ, (size, cnt, cnt_block) in stats:
        print(typ, size, cnt, cnt_block)


    print()
    stats = list(stats_blk.items())
    stats.sort(key=lambda a: a[1], reverse=True)
    for typ, (size, cnt_block, cnt) in stats:
        print(typ, size, cnt_block, cnt)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: blend_stat.py [-v] file.blend")
        quit(1)

    if len(sys.argv) > 2 and sys.argv[1] == "-v":
        verbose = True
        filename = sys.argv[2]
    else:
        filename = sys.argv[1]

    with open(filename, "rb") as f:
       stat_file(f)
