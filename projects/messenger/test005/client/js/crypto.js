
function randomBigInt(bytes) {
	var array = new Uint8Array(bytes);
	window.crypto.getRandomValues(array);

	n = BigInt(0);
	m = BigInt(2**8);
	for (var i = 0; i < array.length; i++) {
	  n = n*m + BigInt(array[i]);
	}
	return n;
}	

function generateSecret() {
	return randomBigInt(secretLength);
}