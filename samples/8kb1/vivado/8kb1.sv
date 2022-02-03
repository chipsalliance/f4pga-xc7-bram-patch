// Copyright 2020-2022 F4PGA Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
// SPDX-License-Identifier: Apache-2.0

module top(
input logic clk,
input logic[12:0] raddr,
input logic[12:0] waddr,
input logic [0:0] din,
output logic [0:0] dout,
input logic reset);

memory #("patch_test/master/8kb1/init/init.mem", 1, 1, 8192) mem(
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
    input logic[12:0] raddr,
    input logic[12:0] waddr,
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
    
