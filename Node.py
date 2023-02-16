import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

from flask_cors import CORS



host = '0.0.0.0'
port = 5000



class Blockchain:

    def __init__(self):
        self.chain = []
        self.data = None
        self.create_block(proof = 1, previous_hash = '0')
        self.nodes = set()


        

    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'data' : self.data}
        self.data = None
        self.chain.append(block)
        return block
    


    def get_previous_block(self):
        return self.chain[-1]
    


    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str((new_proof**2 - previous_proof**2)**3).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    

    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
    

    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True
    

    
    
    def add_data(self, aadhar, fname, lname, age, dob, address, user, passw):
        self.data = {
            'aadhar' : aadhar,
            'fname' : fname,
            'lname' : lname,
            'age' : age,
            'dob' : dob,
            'address' : address,
            'user' : user,
            'pass' : passw
        }
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    

    
    
    def add_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)


        
    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    longest_chain = chain
                    max_length = length
        if longest_chain:
            self.chain = longest_chain
            return True
        else:
            return False
        
        
    
    
app = Flask(__name__)
CORS(app)



blockchain = Blockchain()




@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Checking if the Blockchain is valid
@app.route('/get_node_status', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All Good'}
    else:
        response = {'message': 'Corrupted'}
    return jsonify(response), 200



@app.route('/search_aadhar', methods = ['POST'])
def search_aadhar():
    json = request.get_json()
    data_keys = ['aadhar']
    if not all (key in json for key in data_keys):
        return "Some Elements are missing", 400
    for block in blockchain.chain:
        if block["index"] == 1:
            continue
        elif block["data"]["aadhar"] == json["aadhar"]:
            response = {'message': '1',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
               'data' : block['data']}
            return jsonify(response), 200
    return jsonify({'message' : '0'}), 200
    
            
    
    


@app.route('/add_data', methods = ['POST'])
def add_data():
    json = request.get_json()
    data_keys = ['fname', 'lname', 'age', 'dob', 'address', 'user', 'pass']
    if not all (key in json for key in data_keys):
        return "Some Elements are missing", 400
    

    for node in blockchain.chain:
        if node["index"] == 1:
            continue
        elif node["data"]["aadhar"] == json["aadhar"]:
            return jsonify({'message' : 'Data already exists'}), 202

    index = blockchain.add_data(aadhar, json['fname'], json['lname'], json['age'], json['dob'], json['address'], json['user'], json['pass'])

    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    
    block = blockchain.create_block(proof, previous_hash)


    response = requests.get(f'http://{host}:{port}/replace_chain')
    if response.json()['message'] == 0:
        response = {'message': 'Data Added Succesfully',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
               'data' : block['data']}
        return jsonify(response), 201
    else:
        for node in blockchain.chain:
            if node["data"]["aadhar"] == json['aadhar']:
                response = {'message': 'Data Added Succesfully',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
               'data' : block['data']}
            return jsonify(response), 201
        
        return "Please try again", 400

@app.route('/user_login', methods = ['POST'])
def user_login():
    json = request.get_json()
    data_keys = ['user', 'pass']
    if not all (key in json for key in data_keys):
        return "Some Elements are missing", 400
    for node in blockchain.chain:
        if node["index"] == 1:
            continue
        elif(node["data"]["user"] == json["user"] and node["data"]["pass"] == json["pass"]):
            response = node["data"]
            response["message"] = "1"
            return jsonify(response), 200
    response = {"message" : "0"}
    return jsonify(response), 202


@app.route('/new_aadhar', methods = ['POST'])
def new_aadhar():
    json = request.get_json()
    data_keys = ['fname', 'lname', 'age', 'dob', 'address', 'user', 'pass']
    if not all (key in json for key in data_keys):
        return "Some Elements are missing", 400
    aadhar = str(uuid4())
    index = blockchain.add_data(aadhar, json['fname'], json['lname'], json['age'], json['dob'], json['address'], json['user'], json['pass'])
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    block = blockchain.create_block(proof, previous_hash)
    
    response = requests.get(f'http://{host}:{port}/replace_chain')
    if response.json()['message'] == 0:
        response = {'message': '1',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
               'data' : block['data']}
        return jsonify(response), 201
    else:
        for node in blockchain.chain:
            if node["data"]["aadhar"] == aadhar:
                response = {'message': '1',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
               'data' : block['data']}
            return jsonify(response), 201
        
        return jsonify({'message': '0'}), 400



@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No Node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message' : 'All nodes are active. The Blockchain contains the following nodes: ',
               'total_nodes' : list(blockchain.nodes)}
    return jsonify(response), 201



@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 1,
                   'new_chain' : blockchain.chain}
    else:
        response = {'message': 0,
                   'actual_chain' : blockchain.chain}
    return jsonify(response), 200



app.run(host = host, port = port)

