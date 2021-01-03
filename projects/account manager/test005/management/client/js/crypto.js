sjcl.random.startCollectors();

function encrypt(key, data) {
	return sjcl.encrypt(key, data);
}
function decrypt(key, data, para,) {
	return sjcl.decrypt(key, data);
}
function generateRandom(bytes, paranoia=0) {
	return sjcl.codec.hex.fromBits(
		sjcl.random.randomWords(Math.ceil(bytes / 4), paranoia)
	).substring(0, 2*bytes);
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
		secrets.push(generateRandom(secretLength));
	}
	return secrets;
}
function createPackageKeys(number=1) {
	let keys = []; 
	for(let i = 0; i < number; ++i) {
		keys.push(generateRandom(packageKeyLength));
	}
	return keys;
}
function calculateAccountKey(secret) {
	for(let i = 0; i < accountKeyCycles; ++i) {
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