# Copyright Flexday Solutions LLC, Inc - All Rights Reserved
# Unauthorized copying of this file, via any medium is strictly prohibited
# Proprietary and confidential
# See file LICENSE.txt for full license details.

import boto3
from utils.env_config import AWS_CONFIG, APP_CONFIG

# Initialize the KMS client
kms_client = boto3.client('kms', region_name=AWS_CONFIG.KMS_REGION)  # Set your AWS region

# Define the KMS key ID (replace with your own KMS key ID)
KMS_KEY_ID = AWS_CONFIG.KMS_KEY_ID

def encrypt(data: str) -> str:
    """
    Encrypts the given plaintext using AWS KMS.
    
    :param data: The plaintext string to encrypt.
    :return: Encrypted data in hexadecimal string format.
    """
    if not APP_CONFIG.ENABLE_ENCRYPT:
        return data 
    try:
        # Encrypt the plaintext data
        encrypted_response = kms_client.encrypt(
            KeyId=KMS_KEY_ID,
            Plaintext=data.encode('utf-8')
        )
        
        # Return the encrypted data as a hex string
        encrypted_data = encrypted_response['CiphertextBlob']
        return encrypted_data.hex()
    
    except Exception as e:
        raise Exception(f"Error encrypting data: {str(e)}")


def decrypt(encrypted_data: str) -> str:
    """
    Decrypts the given ciphertext using AWS KMS.
    
    :param encrypted_data: The encrypted data in hexadecimal string format.
    :return: The decrypted plaintext string.
    """
    if not APP_CONFIG.ENABLE_ENCRYPT:
        return encrypted_data 
    try:
        # Convert the encrypted data from hex back to binary
        encrypted_data_bytes = bytes.fromhex(encrypted_data)

        # Decrypt the ciphertext
        decrypted_response = kms_client.decrypt(
            CiphertextBlob=encrypted_data_bytes
        )

        # Return the decrypted data as a string
        decrypted_data = decrypted_response['Plaintext'].decode('utf-8')
        return decrypted_data

    except Exception as e:
        raise Exception(f"Error decrypting data: {str(e)}")
