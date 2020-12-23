let async = (function() {
	return {
		gathering: function(method) {
            let blockerCount = 0;
            let allowExecution = false;
            let executed = true;
            return {
                block: function() {
                    blockerCount += 1;
                },
                unblock: function() {
                    blockerCount -= 1;
                    if(blockerCount < 0) {
                    	blockerCount = 0;
                    }
                    if(blockerCount == 0 && allowExecution == true && executed == false) {
                    	executed = true;
                        if(method){
                            method();
                        }
                    }
                },
                allow: function() {
                    allowExecution = true;
                    this.block();
                    this.unblock();
                }
            };
		}
	}
})()