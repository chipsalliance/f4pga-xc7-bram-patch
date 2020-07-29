module top(
input logic clk,
input logic[6:0] raddr1,
input logic[6:0] raddr2,
input logic[6:0] radd3r,
input logic[6:0] raddr4,
input logic[6:0] waddr1,
input logic [0:0] din,
output logic [0:0] dout1,
output logic [0:0] dout2,
output logic [0:0] dout3,
output logic [0:0] dout4,
input logic reset);

memory #("./128b1/init/init.mem", 1, 1, 128) mem(
	.clk(clk), 
	.raddr1(raddr1), 
	.raddr2(raddr2), 
	.raddr3(raddr3), 
	.raddr4(raddr4), 
	.waddr(waddr), 
	.din(din), 
	.dout1(dout1), 
	.dout2(dout2), 
	.dout3(dout3), 
	.dout4(dout4), 
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
    input logic[6:0] raddr1, raddr2, raddr3, raddr4,
    input logic[6:0] waddr,
    input logic[WID_MEM-1:0] din,
    output logic[WID_MEM-1:0] dout1, dout2, dout3, dout4,
    input logic reset);

    (* ram_style = "block" *) logic [WID_MEM-1:0] ram [0:DEPTH_MEM-1];
    
    if (INIT_ISHEX)
        initial $readmemh(F_INIT, ram);
        //initial $readmemh ("../init/1_by_16k.txt",ram);
    else
        initial $readmemb(F_INIT,ram);
    
    always_ff @(posedge clk) begin
        dout1 <= ram[raddr1];
        dout2 <= ram[raddr2];
        dout3 <= ram[raddr3];
        dout4 <= ram[raddr4];
        ram[waddr]<= din; 
    end
endmodule
    