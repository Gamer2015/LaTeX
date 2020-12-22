window.onload = function() {
	database.init(function() {
		database.initializeMemory(function() { 
			display();

			let serverName = 'localhost';
			let socketPort = 8080;
			let wsUrl = 'ws://'+serverName+':'+socketPort;
			websocket.init(wsUrl);
		});
	});
};