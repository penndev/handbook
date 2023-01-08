
# 虚拟设备 tap/tun 设备

1.创建TUN设备：
`sudo ip tuntap add dev tun0 mode tun`


2.启用TUN设备： 
`sudo ip link set dev tun0 up`

3.为TUN设备设置IP地址：

`sudo ip addr add dev tun0 10.0.0.1/24`

> 这将为TUN设备分配IP地址10.0.0.1，并将其连接到子网10.0.0.0/24。
