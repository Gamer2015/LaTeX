"use strict";

import './board.js';

export class Game {
	constructor(
		rows = 8, cols = 8
		) {
		this.rows 		= rows;
		this.cols 		= cols;

		this.running 	= true;

		/*
		this.canvas 	= canvas;
		this.squareSize = 64;
		this.colorWhite = colorWhite;
		this.colorBlack = colorBlack;
		*/

		this.pieces = [

		]

		this.boards = [new Board(rows, cols)];
	}

	render(canvas, squareSize, colorWhite='efefef', colorBlack='101010') {

	}

	running() {
		return this.running;
	}
}