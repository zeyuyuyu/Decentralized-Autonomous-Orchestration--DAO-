import os
import asyncio
import multiprocessing as mp
from typing import List, Tuple

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

class SecureMultiPartyComputation:
    def __init__(self, num_parties: int, threshold: int):
        self.num_parties = num_parties
        self.threshold = threshold
        self.private_keys = [rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        ) for _ in range(num_parties)]
        self.public_keys = [key.public_key() for key in self.private_keys]

    async def compute(self, inputs: List[bytes]) -> bytes:
        assert len(inputs) == self.num_parties
        
        # Distribute shares of inputs
        shares = await asyncio.gather(*[self._share_input(i, inputs[i]) for i in range(self.num_parties)])

        # Collect and reconstruct the result
        result = await self._reconstruct_result(shares)
        return result

    async def _share_input(self, party_id: int, input_data: bytes) -> List[Tuple[int, bytes]]:
        shares = []
        for i in range(self.num_parties):
            if i == party_id:
                continue
            share = self.public_keys[i].encrypt(input_data, rsa.OAEP(
                mgf=rsa.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            ))
            shares.append((i, share))
        return shares

    async def _reconstruct_result(self, shares: List[List[Tuple[int, bytes]]]) -> bytes:
        result = b''
        for i in range(self.num_parties):
            partial_shares = [share[1] for share in shares if share[0] == i]
            if len(partial_shares) >= self.threshold:
                result += self.private_keys[i].decrypt(b''.join(partial_shares), rsa.OAEP(
                    mgf=rsa.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                ))
        return result

if __name__ == '__main__':
    smp = SecureMultiPartyComputation(num_parties=5, threshold=3)
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(smp.compute([b'input1', b'input2', b'input3', b'input4', b'input5']))
    print(result.decode())
