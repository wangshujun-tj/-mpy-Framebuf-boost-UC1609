# MicroPython ST7567 LCD driver, SPI interfaces

from micropython import const
import framebuf
import time

class UC1609(framebuf.FrameBuffer):
    
    def __init__(self, width, height):
        
        self.width = width
        self.height = height
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        if self.rot==0 or self.rot==2:
            super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB, self.width)
        else:
            super().__init__(self.buffer, self.height, self.width, framebuf.MONO_HMSB, self.height)
        self.init_display()

    def init_display(self):
        if self.res==None:
            self.write_cmd(0xe2)
        else:
            self.res(1)
            time.sleep_ms(10)
            self.res(0)
            time.sleep_ms(100)
            self.res(1)
        time.sleep_ms(10)
        cmd_list=[
            0xae,  #禁用显示，避免未清理的ram数据显示
            0x24,  #设置温度补偿24-27
            0x2c,  #设置电源控制28-2f
            0xeb,  #设置Bias Ratio e8-eb
            0x81,0xb4,  #设置 PM[7:0]
            0x40,  #Set Scroll Line  40-7f
            0x33,0x2a,  #Set APC[R][7:0],
            0xc4,  #Set LC[2:1]
            0xf1,0x3f,  #Set COM End
            ]
        if self.rot==0:
            cmd_list.extend([
            0xC4,   #显示方向调整，行镜像
            0x89,   #数据写自增，行优先
            ])
        elif self.rot==1:
            cmd_list.extend([
            0xC0,   #显示方向调整，原始
            0x8B,   #数据写自增，列优先
            ])            
        elif self.rot==2:
            cmd_list.extend([
            0xC2,   #显示方向调整，列镜像
            0x89,   #数据写自增，行优先
            ])            
        elif self.rot==3:
            cmd_list.extend([
            0xC6,   #显示方向调整，行列镜像
            0x8B,   #数据写自增，列优先
            ])
       
        for cmd in cmd_list:  
            self.write_cmd(cmd)
        self.fill(0)
        self.show()
        self.poweron()
        
    def poweroff(self):
        self.write_cmd(0xae)

    def poweron(self):
        self.write_cmd(0xaf)

    def contrast(self, contrast):
        self.write_cmd(0x20|(contrast&0x07))

    def invert(self, invert):
        self.write_cmd(0x21 | (invert >0))

    def show(self):
        self.write_cmd(0xb0)
        self.write_cmd(0x10)
        self.write_cmd(0x00)
        self.write_data(self.buffer)
        return

class UC1609_I2C(UC1609):
    def __init__(self, width, height, i2c, addr=0x3C, res=None, rot=1):
        self.i2c = i2c
        self.addr = addr
        self.res = res
        self.rot=rot
        if res!=None:
            res.init(res.OUT, value=0)
        super().__init__(width, height)
    def write_cmd(self, cmd):
        self.i2c.writeto(self.addr, bytearray([cmd]))
    def write_data(self, buf):
        self.i2c.writeto(self.addr+1, buf)

class UC1609_SPI(UC1609):
    def __init__(self, width, height, spi, dc=None, res=None, cs=None, rot=1):
        if res!=None:
            res.init(res.OUT, value=0)
            self.res = res
        if dc==None or cs==None:
            print("Must provide a cs and dc")
            return
        dc.init(dc.OUT, value=0)
        cs.init(cs.OUT, value=1)
        self.spi = spi
        self.dc = dc
        self.cs = cs
        self.rot=rot
        super().__init__(width, height, res=None, rot=rot)

    def write_cmd(self, cmd):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)