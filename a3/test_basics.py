#!/usr/bin/env python3
'''
test_basics.py

pytest basics of hashtable RPCs

Author: Xavier Reese
Date: 6 Feb 2026
'''
import os
import hashlib
from HashTableClient import HashTableClient
import pytest
import socket

TEST_FILE = "test_input.txt"
DOWNLOADED_FILE = "test_output.txt"

# -- Fixture --

@pytest.fixture(scope="module")
def client():
    c = HashTableClient(socket.gethostname(), 9246)
    c.connect()
    return c


@pytest.fixture
def cleanup_files():
    yield
    if os.path.exists(TEST_FILE):
        os.remove(TEST_FILE)
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)


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

# ---------- Tests ----------

def test_insert_and_lookup(client):
    client.insert("key1", "hello world")

    value = client.lookup("key1")

    assert value == "hello world"


def test_missing_lookup(client):
    value = client.lookup("does_not_exist")

    assert value is None


def test_remove(client):
    client.insert("key1", "delete me")

    result = client.remove("key1")

    assert result

    value = client.lookup("key1")

    assert value is None

def test_size(client):

    initial_size = client.size()

    client.insert("size1", "a")
    client.insert("size2", "b")

    new_size = client.size()

    client.remove("size1")
    client.remove("size2")

    assert new_size is initial_size + 2


def test_query(client):
    client.insert("query_key", "query_value")

    exists = client.query("query_key")
    missing = client.query("nope")

    assert exists is True
    assert missing is False


def test_insert_lookup_file(client):
    
    # file creation
    original_content = """This is a test file.
                          It contains multiple lines."""

    write_test_file(TEST_FILE, original_content)

    original_hash = file_hash(TEST_FILE)

    # insert
    client.insert_file("file_key", TEST_FILE)

    delete_file(TEST_FILE)

    assert not os.path.exists(TEST_FILE)

    # lookup
    client.lookup_file("file_key", DOWNLOADED_FILE)

    assert os.path.exists(DOWNLOADED_FILE)

    downloaded_hash = file_hash(DOWNLOADED_FILE)

    assert downloaded_hash == original_hash
    
    # cleanup
    delete_file(DOWNLOADED_FILE)


def test_lookup_missing_file(client):
    result = client.lookup_file("no_file_key", "missing.txt")

    assert result is False or not os.path.exists("missing.txt")
