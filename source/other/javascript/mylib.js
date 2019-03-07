/* <StandardFunctions> */
/* makes a deep copy up to depth and then a shallow copy 
 *  supported types:
 * - null
 * - Date
 * - Array
 * - Object
 */
deepCopy : function(obj, depth=500) { // the rest is copied as shallow copy
    let copyObject = null;
    if(obj == null) {
        return null;
    } else if(obj instanceof Date) {
        return new Date(obj.valueOf());
    } else {
        copyObject = Array.isArray(obj) ? [] : {};
    }
    
    try {
        for(let key in obj) {
            if(typeof(obj[key]) == 'object' && depth > 0) {
                copyObject[key] = deepCopy(obj[key], depth - 1);
            } else {
                copyObject[key] = obj[key];
            }
        }
    } catch(err) {}
    
    return copyObject;
},