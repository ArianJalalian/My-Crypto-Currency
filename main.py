from blockchain import Blockchain, Block
from transaction import Transaction
from node import Node, AuthorityNode
from ecdsa import SigningKey, VerifyingKey, NIST384p
from client import Client

# Function to generate ECDSA key pair (for client nodes)
def generate_ecdsa_key_pair():
    sk = SigningKey.generate(curve=NIST384p)
    vk = sk.get_verifying_key()
    return sk, vk.to_string().hex()

# def generate_rsa_key_pair():
#     private_key = rsa.generate_private_key(
#         public_exponent=65537,
#         key_size=2048,
#         backend=default_backend()
#     )
#     public_key = private_key.public_key()
#     return private_key, public_key


# Initialize nodes 
nodes = []
# Initialize blockchain and authority nodes
blockchain = Blockchain()
authority_nodes = []
authority_nodes_public_keys = {}

# Generate authority nodes with unique IDs
num_authority_nodes = 3
for i in range(num_authority_nodes): 
    private, public = generate_ecdsa_key_pair()
    anode = AuthorityNode(f"AuthorityNode-{i+1}", private) 
    authority_nodes_public_keys[f"AuthorityNode-{i+1}"] = public
    authority_nodes.append(anode)
    nodes.append(anode)

simple_nodes = []
# Generate nodes with unique IDs
num_simple_nodes = 5
for i in range(num_simple_nodes): 
    node = Node(f"Node-{i+1}")
    simple_nodes.append(node) 
    nodes.append(node)

for node in nodes : 
    for anode in authority_nodes: 
        node.add_authority_node(anode, authority_nodes_public_keys[anode.node_id])

# Generate clients with initial balances
num_clients = 5
initial_balance = 50
clients = []

# Create clients and nodes
for i in range(num_clients): 
    # sk, vk = generate_ecdsa_key_pair()
    client = Client()  # Create client instance
    clients.append(client)

    for node in nodes:
        node.balances[client.get_address()] = initial_balance

at1 = authority_nodes[0] 
at2 = authority_nodes[1]
at3 = authority_nodes[2] 

n1 = simple_nodes[0]
n2 = simple_nodes[1] 
n3 = simple_nodes[2]
n4 = simple_nodes[3] 
n5 = simple_nodes[4] 

at1.neighbors.extend([n1, n2])
at2.neighbors.extend([n3, n4]) 
at3.neighbors.extend([n5]) 

n1.neighbors.extend([at1]) 
n2.neighbors.extend([at1, n3]) 
n3.neighbors.extend([at2, n2])
n4.neighbors.extend([at2, n5]) 
n5.neighbors.extend([at3, n4])

t1 = clients[0].create_transaction(clients[1].get_address(), 30)  
t2 = clients[0].create_transaction(clients[1].get_address(), 20) 

# Round-robin selection of authority nodes for block mining
current_authority_index = 0

# Main loop to simulate blockchain operation 
n1.add_transaction(t1)   
n5.add_transaction(t2)
for i in range(10):  # Number of blocks to mine  
    authority_node = authority_nodes[current_authority_index]
    mined_block = authority_node.create_new_block()
    
    if mined_block:
        # Add mined block to the blockchain
        blockchain.add_block(mined_block)
        print(f"Block mined by {authority_node.node_id}: {mined_block}")
    
    # for node in nodes:
    #     print(f'{node.node_id} : ')
    #     print(node.mempool)
    # Move to the next authority node in round-robin fashion
    current_authority_index = (current_authority_index + 1) % len(authority_nodes)  

     


# Print final blockchain state
print("\nFinal Blockchain State:")
print(len(at3.blockchain.get_last_block().transactions))

# Print final balances of clients
for node in nodes: 
    print(f'Node {node.node_id} list of balances:') 
    for id, balance in node.balances.items():
        print(f"Client ID: {5}, Balance: {balance}")
