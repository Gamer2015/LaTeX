function getLogLevel(level) {
	level = level.toLowerCase();
	if(level == 'off')
		return 8000;
	if(level == 'error')
		return 7000;
	if(level == 'warning')
		return 6000;
	if(level == 'info') 
		return 5000;
	if(level == 'debug')
		return 4000;
	if(level == 'trace')
		return 3000
	if(level == 'all')
		return 2000;
}

let logLevel = getLogLevel('debug');

function error(...args) {
	if(logLevel <= getLogLevel('error')) {
		console.error(...args);
	}
}
function warn(...args) {
	if(logLevel <= getLogLevel('warning')) {
		console.warn(...args);
	}
}
function info(...args) {
	if(logLevel <= getLogLevel('info')) {
		console.info(...args);
	}
}
function debug(...args) {
	if(logLevel <= getLogLevel('debug')) {
		console.log(...args);
	}
}
function trace(...args) {
	if(logLevel <= getLogLevel('trace')) {
		console.log(...args);
	}
}
function all(...args) {
	if(logLevel <= getLogLevel('all')) {
		console.log(...args);
	}
}
/*
error('error')
warn('warn')
info('info')
debug('debug')
trace('trace')
all('all')
*/