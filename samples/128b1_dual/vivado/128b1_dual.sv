module top(
input logic clk,
input logic[6:0] raddr,
input logic[6:0] waddr,
input logic [1:0] din,
output logic [1:0] dout,
input logic reset);

memory #("samples/128b1_dual/init/init.mem", 1, 1, 128) mem1(
	.clk(clk), 
	.raddr(raddr), 
	.waddr(waddr), 
	.din(din[0]), 
	.dout(dout[0]), 
	.reset(reset));

mymem #("samples/128b1_dual/init/init.mem", 1, 1, 128) mem2(
	.clk(clk), 
	.raddr(raddr), 
	.waddr(waddr), 
	.din(din[1]), 
	.dout(dout[1]), 
	.reset(reset));

endmodule
 
module mymem #(
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

  memory #("samples/128b1_dual/init/init.mem", 1, 1, 128) mem2a(
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
    
