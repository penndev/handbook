- [查看概况](./filesystem.md#show)
- [分区挂载](./filesystem.md#mount)
- *LVM*
  - [LVM合并硬盘并分区](./filesystem.md#lvm_merge)
  - [LVM移除分区](./filesystem.md#lvm_remove)

---

## 概况查看 {#show}
** 查看已经挂载的文件系统 **
```bash
df -hT
``` 
- `h` --human-readable
- `T` --print-type

** 查看全部设备的文件系统 ** 
```bash
lsblk
lsblk -afp         
```
- `a` --all
- `f` --fs
- `p` --paths
** 查看分区表 ** 
- `fdisk -l` 查看分区表
- `parted -l` 查看分区表

## 分区挂载 {#mount}
- `mount /dev/sda /home` 挂载做好文件系统的硬盘到目录  
- `umount /home`   取消挂载
- `vim /etc/fstab` 编辑fstab使文件系统开机就挂载。
- `mount -a`       进行fstab修改生效，可检查配置状态。
- `df -hT` 查看挂在的情况

## LVM逻辑卷
> LVM（Logical Volume Manager，逻辑卷管理器）是一种用于在Linux系统中管理磁盘存储空间的软件工具。

### LVM合并硬盘并分区 {#lvm_merge}
> 目标 将新增的三块硬盘`/dev/nvme0n1`,`/dev/nvme1n1`,`/dev/nvme2n1` 每块8T的硬盘 组合一块挂载到`/home`

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
```
3. 制作文件系统
    ```bash
    lvcreate -l 100%FREE -n lv_date vg_home

    mkfs.xfs /dev/vg_home/lv_date
    ```
4. 挂载文件系统
    ```bash
    mount /dev/vg_home/lv_date /home

    vi /etc/fstab

    /dev/vg_home/lv_date  /home  xfs  defaults  0  2

    mount -a
    ```

### LVM移除分区 {#lvm_remove}
> 如下，目标移除系统的lvm /dev/mapper/centos-root /home 分区

```bash
[root@localhost ~]# df -h /home
文件系统                 容量  已用  可用 已用% 挂载点
/dev/mapper/centos-root   50G   21G   30G   41% /
```
1. 首先移除挂在分区 `umount /home`, `vi /etc/fstab` 中的分区信息
2. `lvremove /dev/mapper/centos-home` 删除分区

### LVM拓展分区 {#lvm_remove}

1. `lvextend -l +100%FREE /dev/mapper/centos-root` 将所有的剩余空间全部分配给指定的分区
2. 调整文件系统大小
  - `xfs_growfs /{DIR}` xfs文件系统
  - `resize2fs {DEV}` ext文件系统 
