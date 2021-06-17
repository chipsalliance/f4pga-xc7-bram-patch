// Copyright (C) 2020-2021  The Project U-Ray Authors.
//
// Use of this source code is governed by a ISC-style
// license that can be found in the LICENSE file or at
// https://opensource.org/licenses/ISC
//
// SPDX-License-Identifier: ISC

module top(
input logic clk,
input logic[6:0] raddr,
input logic[6:0] waddr,
input logic [0:0] din,
output logic [0:0] dout,
input logic reset);

memory #("tests/master/128b1/init/init.mem", 1, 1, 128) mem(
	.clk(clk), 
	.raddr(raddr), 
	.waddr(waddr), 
	.din(din), 
	.dout(dout), 
	.reset(reset));

endmodule
 
module memory #(
    parameter F_INIT="init.txt",
    parameter INIT_ISHEX = 1,
    //parameter WID_MEM=16,
    //parameter DEPTH_MEM=2048)
    parameter WID_MEM=1,
    parameter DEPTH_MEM=16384)    
    (input logic clk,
    input logic[6:0] raddr,
    input logic[6:0] waddr,
    input logic[WID_MEM-1:0] din,
    output logic[WID_MEM-1:0] dout,
    input logic reset);

    (* ram_style = "block" *) logic [WID_MEM-1:0] ram [0:DEPTH_MEM-1];
    
    if (INIT_ISHEX)
        initial $readmemh(F_INIT, ram);
        //initial $readmemh ("../init/1_by_16k.txt",ram);
    else
        initial $readmemb(F_INIT,ram);
    
    always_ff @(posedge clk) begin
        dout <= ram[raddr];
        ram[waddr]<= din; 
    end
endmodule
    
