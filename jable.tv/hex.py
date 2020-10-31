from binascii import hexlify, unhexlify


def read_hex_file(file):
    with open(file, 'rb') as f:
        data = f.read()
        return hexlify(data).decode("utf-8")


if __name__ == "__main__":
    data = read_hex_file('16c5db5e518699c4.ts')
    print(data.decode("utf-8"))

# openssl aes-128-cbc -d -in 001.ts -out fileSequence0_decrypto.ts -nosalt -iv 962ec00083ed2a46d7c1c8a8271157c3 -K c8a9ded8b41a7daa57e224968934f86f
# openssl aes-128-cbc -d -in 000.ts -out fileSequence0_decrypto.ts -nosalt -iv 03db44e74c19e9df04f59c9ff45e7090 -K A0B104918D826543148C60B4365C4121
