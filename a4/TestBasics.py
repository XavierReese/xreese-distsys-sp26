#!/usr/bin/env python3
'''
TestBasics.py

test basics of hashtable RPCs

Author: Xavier Reese
Date: 6 Feb 2026
'''
import os
import hashlib
from HashTableClient import HashTableClient

TEST_FILE = "test_input.txt"
DOWNLOADED_FILE = "test_output.txt"


# ---------- Helpers ----------

def file_hash(filename):
    with open(filename, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def write_test_file(filename, content):
    with open(filename, "w") as f:
        f.write(content)


def delete_file(filename):
    if os.path.exists(filename):
        os.remove(filename)


def print_test(name):
    print(f"\n=== {name} ===")


def assert_true(condition, message):
    if condition:
        print(f"PASS: {message}")
    else:
        print(f"FAIL: {message}")


def assert_equal(a, b, message):
    if a == b:
        print(f"PASS: {message}")
    else:
        print(f"FAIL: {message}")
        print("Expected:", b)
        print("Actual:", a)


# ---------- Tests ----------

def tests(client):

    # Basic Insert & Lookup

    print_test("Insert and Lookup")

    client.insert("key1", "hello world")

    value = client.lookup("key1")

    assert_equal(value, "hello world", "lookup returns inserted value")


    # Basic Missing Lookup

    print_test("Lookup Missing Key")

    value = client.lookup("does_not_exist")

    assert_equal(value, None, "lookup missing returns None")


    # Basic Removal

    print_test("Remove Key")

    client.insert("key1", "delete me")

    result = client.remove("key1")

    assert_true(result, "remove returns True")

    value = client.lookup("key1")

    assert_equal(value, None, "removed key no longer exists")


    # Size

    print_test("Size")

    initial_size = client.size()

    client.insert("size1", "a")
    client.insert("size2", "b")

    new_size = client.size()

    client.remove("size1")
    client.remove("size2")

    #print(f"Initial: {initial_size}, New: {new_size}")

    assert_true(new_size == initial_size + 2, "size increased correctly")


    # Query

    print_test("Query")

    client.insert("query_key", "query_value")

    exists = client.query("query_key")
    missing = client.query("nope")

    assert_true(exists == True, "query existing key")
    assert_true(missing == False, "query missing key")


    # Insert & Lookup FILE

    print_test("Insert File and Lookup File")

    # create file
    original_content = """This is a test file.
It contains multiple lines.
"""

    write_test_file(TEST_FILE, original_content)

    original_hash = file_hash(TEST_FILE)

    # insert
    client.insert_file("file_key", TEST_FILE)

    delete_file(TEST_FILE)

    assert_true(not os.path.exists(TEST_FILE), "local file deleted")

    # lookup
    client.lookup_file("file_key", DOWNLOADED_FILE)

    assert_true(os.path.exists(DOWNLOADED_FILE), "file downloaded")

    downloaded_hash = file_hash(DOWNLOADED_FILE)

    assert_equal(downloaded_hash, original_hash, "downloaded file matches original")
    
    # cleanup
    delete_file(DOWNLOADED_FILE)


    # Lookup Missing File

    print_test("Lookup Missing File")

    result = client.lookup_file("no_file_key", "missing.txt")

    assert_true(result == False or not os.path.exists("missing.txt"), "lookup_file missing fails correctly")


# ---------- Main ----------

def main(host, port):

    client = HashTableClient(host, port)

    client.connect()

    tests(client)

    print("\nAll tests complete.")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: TestBasics.py hostname port")
        exit(0)
    host = sys.argv[1]
    port = int(sys.argv[2])
    main(host, port)
