import struct
from collections import defaultdict
import json


class StoragePolicy:
    @staticmethod
    def dump(word_to_docs_mapping, filepath: str):
        pass

    @staticmethod
    def load(filepath: str):
        pass


class JSONPolicy(StoragePolicy):
    @classmethod
    def dump(cls, word_to_docs_mapping, filepath: str):
        with open(filepath, 'w', encoding='utf-8') as file:
            json.dump(word_to_docs_mapping, file)

    @classmethod
    def load(cls, filepath: str):
        with open(filepath) as file:
            word_to_docs_mapping = json.loads(file.read())
        return word_to_docs_mapping


class StructPolicy(StoragePolicy):
    @classmethod
    def dump(cls, word_to_docs_mapping, filepath: str):
        with open(filepath, 'wb') as file:
            count = struct.pack('>i', len(word_to_docs_mapping))
            file.write(count)
            for key in word_to_docs_mapping:
                key_encoded = key.encode('utf-8')
                key_len = len(key_encoded)
                key_len_bin = struct.pack('>h', key_len)
                file.write(key_len_bin)

                format_str = '>' + str(key_len) + 's'
                key_str_bin = struct.pack(format_str, key_encoded)
                file.write(key_str_bin)

                doc_len = len(word_to_docs_mapping[key])
                doc_len_bin = struct.pack('>h', doc_len)
                file.write(doc_len_bin)

                for doc_id in word_to_docs_mapping[key]:
                    doc_id_bin = struct.pack('>h', doc_id)
                    file.write(doc_id_bin)

    @classmethod
    def load(cls, filepath: str):
        with open(filepath, 'rb') as file:
            count_bin = file.read(4)
            count = struct.unpack('>i', count_bin)[0]
            word_to_docs_mapping = defaultdict(list)
            for _ in range(count):
                key_len_pack = file.read(2)
                key_len = struct.unpack('>h', key_len_pack)[0]

                format_str = '>' + str(key_len) + 's'
                decoding_str = file.read(key_len)
                bin_str = struct.unpack(format_str, decoding_str)[0]
                key = bin_str.decode('utf-8')

                index_len_pack = file.read(2)
                index_len = struct.unpack('>h', index_len_pack)[0]

                decoding_list = file.read(2 * index_len)
                format_int = '>' + str(index_len) + 'h'
                doc_id_list = list(struct.unpack(format_int, decoding_list))
                word_to_docs_mapping[key] = doc_id_list

        return word_to_docs_mapping
