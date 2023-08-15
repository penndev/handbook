# Linux 硬盘与分区

> 分区是物理硬盘的逻辑处理，可以将一块硬盘分割位多个分区。也可以将多个硬盘合并为单个分区。

- `lsblk -l` 查看分区情况

- `fdisk -l` 

- `parted -l`


## 一个硬盘拆分多个逻辑分区

...

## 合并多个硬盘到一个逻辑分区

> 目标 将新增的三块硬盘`/dev/nvme0n1`,`/dev/nvme1n1`,`/dev/nvme2n1` 每块8T的硬盘 组合一块挂载到home


1. 初始化物理卷 

```bash
pvcreate /dev/nvme0n1 /dev/nvme1n1 /dev/nvme2n1
或
pvcreate /dev/nvme0n1 
pvcreate /dev/nvme1n1 
pvcreate /dev/nvme2n1
```

2. 创建新卷组

```bash
vgcreate vg_home /dev/nvme0n1 /dev/nvme1n1 /dev/nvme2n1
或
vgcreate vg_home /dev/nvme0n1 
vgextend vg_home /dev/nvme1n1 
vgextend vg_home /dev/nvme2n1
-- 先创建再添加
```

3. 创建逻辑卷

```bash
lvcreate -l 100%FREE -n lv_date vg_home

mkfs.xfs /dev/vg_home/lv_date
```

4. 挂载文件系统

```bash
mount /dev/vg_home/lv_date /home

vi /etc/fstab

/dev/sda

/dev/vg_home/lv_date  /home  ext4  defaults  0  2
```