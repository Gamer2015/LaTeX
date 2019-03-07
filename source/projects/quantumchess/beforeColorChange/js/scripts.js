'use strict';


import './game.js';

let canvas 		= document.getElementById("myCanvas");
let squareSize 	= 64;
let colorWhite 	='#efefef';
let colorBlack 	='#101010';

let logging = true;

function log(logging, level, message) {
	if(logging == true) {
		if(typeof(level) != 'string') {
			level = 'ALL';
		}
		console.log(level.trim().toUpperCase(), '|', message);
	}
}

function handleKeyEvent(event, input) {
    let key = event.keyCode;
    if(key == 13) {
    	input.onblur(input.value);
    }
}

function setCanvasId(canvasId) {
	canvas 		= document.getElementById(canvasId);
}
function setSquareSize(newSquareSize) {
	squareSize 	= newSquareSize;
}
function setColorWhite(newColorWhite) {
	colorWhite 	= newColorWhite;
}
function setColorBlack(newColorBlack) {
	colorBlack 	= newColorBlack;
}

function newGame(logging=true) {
	log(logging, 'debug', "newGame");	
}

function saveGame() {
	console.log("saveGame");
}

function openGame() {
	console.log("openGame");
}



function main(logging) {
	
}
main(logging);