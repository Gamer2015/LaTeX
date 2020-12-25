function encrypt(key, data) {
	return sjcl.encrypt(key, data);
}
function decrypt(key, data, para,) {
	return sjcl.decrypt(key, data);
}
function generateRandom(bytes, paranoia=0) {
	return sjcl.codec.hex.fromBits(sjcl.random.randomWords(bytes, paranoia));
}
function generateMessageIds(number=1) {
	let messageIds = [];
	for(let i = 0; i < number; ++i) {
		messageIds.push(generateRandom(requestTokenLength));
	}
	return messageIds;
}
function generateSecrets(number=1) {
	let secrets = [];
	for(let i = 0; i < number; ++i) {
		secrets.push(sjcl.codec.hex.fromBits(sjcl.random.randomWords(secretLength, 0)))
	}
	return secrets;
}
function calculateEncryptionKey(secret) {
	for(let i = 0; i < dataKeyCycles; ++i) {
		secret = sjcl.codec.hex.fromBits(sjcl.hash.sha256.hash(secret))
	}
	return secret;
}
function calculatePassword(secret) {
	for(let i = 0; i < passwordCycles; ++i) {
		secret = sjcl.codec.hex.fromBits(sjcl.hash.sha256.hash(secret))
	}
	return secret;
}