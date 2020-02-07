import hashlib
from datetime import datetime, timezone
from typing import List, Any, Dict, AnyStr, Union, Generator

from chainpoint.chainpoint import MerkleTools
from jsonpath_rw import parse, Root, Child, Fields, DatumInContext
from pycoin.serialize import h2b


def hash_byte_array(data):
    hashed = hashlib.sha256(data).hexdigest()
    return hashed


def ensure_string(value: AnyStr) -> str:
    if isinstance(value, str):
        return value
    return value.decode('utf-8')


class MerkleTree(object):
    """Representation of a Merkle Tree.

    More at https://en.wikipedia.org/wiki/Merkle_tree.
    """

    def __init__(self):
        self.tree = MerkleTools(hash_type='sha256')

    def populate(self, node_generator: Generator) -> None:
        """
        Populate Merkle Tree with data from node_generator. This requires that node_generator yield byte[] elements.
        Hashes, computes hex digest, and adds it to the Merkle Tree
        :param node_generator:
        :return:
        """
        for data in node_generator:
            hashed = hash_byte_array(data)
            self.tree.add_leaf(hashed)

    def get_root(self, binary=False) -> bytearray:
        """
        Finalize tree and return the Root, a byte array to anchor on a blockchain tx.
        :return:
        """
        self.tree.make_tree()
        merkle_root = self.tree.get_merkle_root()
        if binary:
            return h2b(ensure_string(merkle_root))
        return ensure_string(merkle_root)

    def get_proof_generator(self, tx_id: AnyStr, signature_type: AnyStr, chain_name: AnyStr) -> Dict:
        """
        Returns a generator of Merkle Proofs in insertion order.

        :param tx_id: blockchain transaction id
        :return:
        """
        root = ensure_string(self.tree.get_merkle_root())
        node_count = len(self.tree.leaves)
        for index in range(0, node_count):
            proof = self.tree.get_proof(index)
            proof2 = []

            for p in proof:
                dict2 = dict()
                for key, value in p.items():
                    dict2[key] = ensure_string(value)
                proof2.append(dict2)
            target_hash = ensure_string(self.tree.get_leaf(index))
            merkle_proof = {
                "type": ['MerkleProof2017', 'Extension'],
                "merkleRoot": root,
                "targetHash": target_hash,
                "proof": proof2,
                "anchors": [{
                    "sourceId": tx_id,
                    "type": signature_type,
                    "chain": chain_name
                }]}
            yield merkle_proof


def validate_required_fields(some_object: Any, required_fields: List) -> None:
    """Raise an exception if any of the required fields are missing from the object."""
    for field in required_fields:
        if not some_object.__getattribute__(field):
            raise Exception(
                f"The field '{field}' is required for object of class '{some_object.__class__.__name__}'."
            )


def validate_required_fields_interactively(some_object: Any, required_fields: List) -> None:
    """Ask for user input if any of the required fields is missing."""
    for field_name in required_fields:
        ask_input_if_missing(some_object, field_name)


def ask_input_if_missing(some_object: Any, field_name: AnyStr, attempt: int = 0, max_retries: int = 2) -> None:
    """Asks the user for input if any of the required fields are missing from the object."""
    if attempt >= max_retries:
        raise Exception(
            f"The field '{field_name}'is missing even after asking for user input, for "
            f"object of class '{some_object.__class__.__name__}'."
        )

    attempt += 1
    if not some_object.__getattribute__(field_name):
        value = input(
            f"The required field '{field_name}' cannot be empty for '{some_object.__class__.__name__}', please enter a "
            f"valid value: "
        )
        some_object.__setattr__(field_name, value)
        if not some_object.__getattribute__(field_name):
            ask_input_if_missing(some_object, field_name, attempt=attempt, max_retries=max_retries)


def factor_in_new_try(number: Union[int, float], try_count: int) -> Union[int, float]:
    """Increase the given number with 10% with each try."""
    factor = float(f"1.{try_count}")
    return int(number * factor)


def create_iso8601_tz() -> str:
    """Get the current datetime in ISO 8601 format."""
    ret = datetime.now(timezone.utc)
    return ret.isoformat()


def get_path(match: 'DatumInContext') -> None:
    """Return an iterator based upon MATCH.PATH. Each item is a path component, start from the outer most item."""
    if match.context is not None:
        for path_element in get_path(match.context):
            yield path_element
        yield str(match.path)


def recurse(child: 'Child', fields_reverse: List) -> None:
    """Recurse fields."""
    if isinstance(child, Fields):
        fields_reverse.append(child.fields[0])
    else:
        if not isinstance(child, Child):
            raise Exception('Unexpected input while recursing for additional fields.')
        if not isinstance(child.left, Root):
            recurse(child.left, fields_reverse)
        recurse(child.right, fields_reverse)


def update_dict(raw_dict: Dict, path: AnyStr, value: AnyStr) -> Dict:
    """Update dictionary's PATH with VALUE. Return updated dict"""
    try:
        first = next(path)
        if first.startswith('[') and first.endswith(']'):
            try:
                first = int(first[1:-1])
            except ValueError:
                pass
        raw_dict[first] = update_dict(raw_dict[first], path, value)
        return raw_dict
    except StopIteration:
        return value


def set_dict_field(raw_dict: Dict, path: AnyStr, value: AnyStr) -> Dict:
    """Set dictionary's `path` with `value`. Return the updated dict"""
    jp = parse(path)
    matches = jp.find(raw_dict)
    if matches:
        for match in matches:
            jsonpath_expr = get_path(match)
            raw_dict = update_dict(raw_dict, jsonpath_expr, value)
    else:
        fields = []
        recurse(jp, fields)
        temp_json = raw_dict
        for idx, f in enumerate(fields):
            if f in temp_json:
                temp_json = temp_json[f]
            elif idx == len(fields) - 1:
                temp_json[f] = value
            else:
                raise (Exception(f"Invalid path : '{'.'.join(fields)}' while setting dict field."))
    return raw_dict


NOW = create_iso8601_tz()
