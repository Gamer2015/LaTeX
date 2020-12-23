function encrypt(key, data) {
	return sjcl.encrypt(key, data);
}
function decrypt(key, data, para,) {
	return sjcl.decrypt(key, data);
}
function generateMessageIds(number=1) {
	let messageIds = [];
	for(let i = 0; i < number; ++i) {
		messageIds.push(sjcl.codec.hex.fromBits(sjcl.random.randomWords(requestTokenLength, 0)))
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
function calculateDataKey(secret) {
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
function calculatePasswords(secrets) {
	if(Array.isArray(secrets) == false) {
		secrets = [secrets];
	}
	for(let i = 0; i < secrets.length; ++i) {
		secrets[i] = calculatePassword(secrets[i])
	}
	return secrets;
}