let alphabets = {
    // base58: '123456789abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ',
    // base33: '123456789ABCDEFGHJKLMNPQRSTUVWXYZ',
    base34: 'abcdefghijkmnopqrstuvwxyz123456789'
};

let base34 = (function(alpha) {
    let alphabet = alpha || alphabets.base34,
        base = BigInt(alphabet.length);
    return {
        encode: function(enc) {
            if(typeof enc==='number' && enc === parseInt(enc)) {
                enc = BigInt(enc);
            }
            if(typeof enc !== 'bigint')
                throw '"encode" only accepts integers.';
            let encoded = '';
            while(enc) {
                let remainder = enc % base;
                enc = enc / base;
                encoded = alphabet[remainder].toString() + encoded;        
            }
            return encoded;
        },
        decode: function(dec) {
            if(typeof dec!=='string')
                throw '"decode" only accepts strings.';            
            let decoded = 0n;
            while(dec) {
                let alphabetPosition = BigInt(alphabet.indexOf(dec[0]));
                if (alphabetPosition < 0)
                    throw '"decode" can\'t find "' + dec[0] + '" in the alphabet: "' + alphabet + '"';
                let powerOf = BigInt(dec.length - 1);
                decoded += alphabetPosition * (base**powerOf);
                dec = dec.substring(1);
            }
            return decoded;
        }
    };
})();

let idEncoding = base34;