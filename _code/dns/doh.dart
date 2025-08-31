// ignore_for_file: unused_import, dead_code


import 'dart:typed_data';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:test/test.dart';

final dio = Dio();

/// 定义 DNS 消息类型的枚举。
/// 1 - 主机地址
/// 2 - 权威名称服务器
/// 3 - 邮件目的地（已废弃 - 使用 MX）
/// 4 - 邮件转发器（已废弃 - 使用 MX）
/// 5 - 别名的规范名称
/// 6 - 标记授权区域的开始
/// 7 - 邮箱域名（实验性）
/// 8 - 邮件组成员（实验性）
/// 9 - 邮件重命名域名（实验性）
/// 10 - 空记录（实验性）
/// 11 - 知名服务描述
/// 12 - 域名指针
/// 13 - 主机信息
/// 14 - 邮箱或邮件列表信息
/// 15 - 邮件交换
/// 16 - 文本字符串
// ignore_for_file: constant_identifier_names
enum DNSMessageType {
  A,
  NS,
  MD,
  MF,
  CNAME,
  SOA,
  MB,
  MG,
  MR,
  NULL,
  WKS,
  PTR,
  HINFO,
  MINFO,
  MX,
  TXT;

  static DNSMessageType toType(int value) {
    switch (value) {
      case 1:
        return DNSMessageType.A;
      case 2:
        return DNSMessageType.NS;
      case 3:
        return DNSMessageType.MD;
      case 4:
        return DNSMessageType.MF;
      case 5:
        return DNSMessageType.CNAME;
      case 6:
        return DNSMessageType.SOA;
      case 7:
        return DNSMessageType.MB;
      case 8:
        return DNSMessageType.MG;
      case 9:
        return DNSMessageType.MR;
      case 10:
        return DNSMessageType.NULL;
      case 11:
        return DNSMessageType.WKS;
      case 12:
        return DNSMessageType.PTR;
      case 13:
        return DNSMessageType.HINFO;
      case 14:
        return DNSMessageType.MINFO;
      case 15:
        return DNSMessageType.MX;
      case 16:
        return DNSMessageType.TXT;
      default:
        // 返回默认值或抛出异常
        throw Exception('DNSMessageType Error $value !');
    }
  }

  // 定义一个方法来获取枚举值对应的整数值
  int toInt() {
    switch (this) {
      case DNSMessageType.A:
        return 1;
      case DNSMessageType.NS:
        return 2;
      case DNSMessageType.MD:
        return 3;
      case DNSMessageType.MF:
        return 4;
      case DNSMessageType.CNAME:
        return 5;
      case DNSMessageType.SOA:
        return 6;
      case DNSMessageType.MB:
        return 7;
      case DNSMessageType.MG:
        return 8;
      case DNSMessageType.MR:
        return 9;
      case DNSMessageType.NULL:
        return 10;
      case DNSMessageType.WKS:
        return 11;
      case DNSMessageType.PTR:
        return 12;
      case DNSMessageType.HINFO:
        return 13;
      case DNSMessageType.MINFO:
        return 14;
      case DNSMessageType.MX:
        return 15;
      case DNSMessageType.TXT:
        return 16;
    }
  }
}

class DNSMessageQuestion {
  /// 请求域名
  String name = "";

  /// 1 获取A值
  DNSMessageType type = DNSMessageType.A;

  /// 1 互联网类型
  /// 其他网络类型不考虑。
  int typeClass = 1;

  DNSMessageQuestion({
    this.name = "",
    this.type = DNSMessageType.A,
    this.typeClass = 1,
  });

  @override
  String toString() {
    return 'DNSMessageQuestion(\n'
        '  name: $name,\n'
        '  type: ${type.toInt()},\n'
        '  typeClass: $typeClass\n'
        ')';
  }
}

class DNSMessageResource extends DNSMessageQuestion {
  /// 存活周期
  int ttl = 0;

  /// 结果长度
  int rdLength = 0;

  String rData = "";

  String toRData(Uint8List bytes, int offset,
      String Function(int position, bool status) pointer) {
    switch (type) {
      case DNSMessageType.A:
        var data = bytes.sublist(offset, offset + rdLength);
        return data.buffer.asUint8List().join('.');
      case DNSMessageType.CNAME:
        return pointer(offset, false);
      case DNSMessageType.TXT:
        var data = bytes.sublist(offset, offset + rdLength);
        return String.fromCharCodes(data);
      default:
        throw Exception('Unknown DNS record type $this');
    }
  }

  @override
  String toString() {
    return 'DNSMessageResource(\n'
        '  name: $name,\n'
        '  type: $type,\n'
        '  typeClass: $typeClass,\n'
        '  ttl: $ttl,\n'
        '  rdLength: $rdLength,\n'
        '  rData: ${rData}\n'
        ')';
  }
}

class DNSMessage {
  int headerID = 0;

  /// 0查询请求 1 返回请求
  int headerQR = 0;

  /// 0 标准查询，
  /// 1 反向查询
  /// 2 服务器状态查询
  /// 3-15 保留
  int headerOpcode = 0;

  /// 权威应答标识，是否存在别名和多个记录
  int headerAA = 0;

  /// 是否是截断位置
  int headerTC = 0;

  /// 是否让服务器进行递归查询（从自身缓存获取）
  int headerRD = 0;

  /// 服务器是否递归查询（从自身缓存获取）
  int headerRA = 0;

  /// 应答标识 0 无错误, 其他都是有发生错误。
  int headerRCODE = 0;

  /// 查询记录数
  int headerQDCount = 0;

  /// 应答记录数
  int headerANCount = 0;

  /// NS记录数
  int headerNSCount = 0;

  /// 额外记录数
  int headerARCount = 0;

  /// 消息查询部分
  List<DNSMessageQuestion> question = [];

  /// 返回结果部分
  List<DNSMessageResource> resource = [];

  Uint8List toUint8List() {
    var bytes = Uint8List(12);
    bytes[0] = (headerID >> 8) & 0xFF;
    bytes[1] = headerID & 0xFF;
    bytes[2] = (headerQR << 7) |
        (headerOpcode << 3) |
        (headerAA << 2) |
        (headerTC << 1) |
        headerRD;
    bytes[3] = (headerRA << 7) | (headerRCODE & 0x0F);
    bytes[4] = (headerQDCount >> 8) & 0xFF;
    bytes[5] = headerQDCount & 0xFF;
    bytes[6] = (headerANCount >> 8) & 0xFF;
    bytes[7] = headerANCount & 0xFF;
    bytes[8] = (headerNSCount >> 8) & 0xFF;
    bytes[9] = headerNSCount & 0xFF;
    bytes[10] = (headerARCount >> 8) & 0xFF;
    bytes[11] = headerARCount & 0xFF;

    List<int> query = [];
    for (var item in question) {
      for (var label in item.name.split('.')) {
        query.add(label.length);
        query.addAll(utf8.encode(label));
      }
      query.add(0);
      var type = item.type.toInt();
      query.add((type >> 8) & 0xFF);
      query.add(type & 0xFF);
      query.add((item.typeClass >> 8) & 0xFF);
      query.add(item.typeClass & 0xFF);
    }
    return Uint8List.fromList([...bytes, ...query]);
  }

  static DNSMessage parse(Uint8List bytes) {
    if (bytes.lengthInBytes < 12) {
      throw ArgumentError('Uint8List too short for DNS message header.');
    }
    var dns = DNSMessage();
    dns.headerID = (bytes[0] << 8) + bytes[1];
    dns.headerQR = bytes[2] >> 7;
    dns.headerOpcode = (bytes[2] >> 3) & 0x0f;
    dns.headerAA = (bytes[2] >> 2) & 0x01;
    dns.headerTC = (bytes[2] >> 1) & 0x01;
    dns.headerRD = (bytes[2]) & 0x01;
    dns.headerRA = (bytes[3] >> 7) & 0x01;
    dns.headerRCODE = bytes[3] & 0x0f;
    dns.headerQDCount = (bytes[4] << 8) + bytes[5];
    dns.headerANCount = (bytes[6] << 8) + bytes[7];
    dns.headerNSCount = (bytes[8] << 8) + bytes[9];
    dns.headerARCount = (bytes[10] << 8) + bytes[11];
    var offset = 12;
    // 开始循环处理
    // 请求段中不会出现压缩。
    for (int i = 0; i < dns.headerQDCount; i++) {
      // 对压缩进行还原。
      var quest = DNSMessageQuestion();
      while (bytes[offset] != 0) {
        offset += 1;
        if (quest.name != "") {
          quest.name += ".";
        }
        quest.name +=
            utf8.decode(bytes.sublist(offset, offset += bytes[offset - 1]));
      }
      offset += 1; //结束标志位 0x00
      var type = (bytes[offset] * 256) + bytes[offset + 1];
      quest.type = DNSMessageType.toType(type);
      offset += 2; // type 2 byte
      quest.typeClass = (bytes[offset] << 8) + bytes[offset + 1];
      offset += 2; // class 2 byte
      dns.question.add(quest);
    }

    /// position 标志位，status 是否更新标志位
    String pointer(int position, bool status) {
      if ((bytes[position] & 0xc0) == 0xc0) {
        if (status) {
          offset += 2; //两个指针位置
        }
        position = (bytes[position] & 0x3f) + bytes[position + 1];
        return pointer(position, false);
      }

      var name = "";
      var len = 0;
      while (bytes[position + len] != 0) {
        if (name != "") {
          name += ".";
        }
        final positionNew = position + len;
        if ((bytes[positionNew] & 0xc0) == 0xc0) {
          position = (bytes[positionNew] & 0x3f) + bytes[positionNew + 1];
          return name + pointer(position, false);
        }
        // 第一个字符开始的位置
        var start = positionNew + 1;
        var end = positionNew + bytes[positionNew] + 1;
        name += utf8.decode(bytes.sublist(start, end));
        len += 1 + bytes[positionNew];
      }
      if (status) {
        offset += len + 1; // 1为结束标志位。
      }
      return name;
    }

    // 开始处理结果段
    for (int i = 0; i < dns.headerANCount; i++) {
      var res = DNSMessageResource();
      res.name = pointer(offset, true);
      var type = (bytes[offset] * 256) + bytes[offset + 1];
      res.type = DNSMessageType.toType(type);
      offset += 2; // type 2 byte
      res.typeClass = (bytes[offset] << 8) + bytes[offset + 1];
      offset += 2; // class 2 byte
      res.ttl = (bytes[offset] << 24) +
          (bytes[offset + 1] << 16) +
          (bytes[offset + 2] << 8) +
          (bytes[offset + 3]);
      offset += 4; // ttl 4 byte
      res.rdLength = (bytes[offset] << 8) + bytes[offset + 1];
      offset += 2; // rdLength 2 byte
      var offsetSet = offset;
      res.rData = res.toRData(bytes, offset, pointer);
      offset = offsetSet + res.rdLength;
      dns.resource.add(res);
    }
    return dns;
  }

  @override
  String toString() {
    return 'DNSMessage(\n'
        '  headerID: $headerID,\n'
        '  headerQR: $headerQR,\n'
        '  headerOpcode: $headerOpcode,\n'
        '  headerAA: $headerAA,\n'
        '  headerTC: $headerTC,\n'
        '  headerRA: $headerRA,\n'
        '  headerRD: $headerRD,\n'
        '  headerRCODE: $headerRCODE,\n'
        '  headerQDCount: $headerQDCount,\n'
        '  headerANCount: $headerANCount,\n'
        '  headerNSCount: $headerNSCount,\n'
        '  headerARCount: $headerARCount,\n'
        '  question: $question,\n'
        ')';
  }

  DNSMessage({
    this.headerID = 0,
    this.headerRD = 0,
    this.headerQDCount = 0,
    List<DNSMessageQuestion>? question,
  }) : question = question ?? [];
}

Future<List<DNSMessageResource>> resolveDOH(
    String srv, String host, DNSMessageType type) async {
  var query = DNSMessage(
      headerID: 10010,
      headerRD: 1,
      headerQDCount: 1,
      question: [DNSMessageQuestion(name: host, type: type)]);
  var queryRow = query.toUint8List();
  var queryUri = base64UrlEncode(queryRow).replaceAll('=', '');
  var resp = await dio.get(
    'https://$srv/dns-query?dns=$queryUri',
    options: Options(
      headers: {
        Headers.acceptHeader: 'application/dns-message',
      },
      responseType: ResponseType.bytes,
    ),
  );
  Uint8List respData = resp.data as Uint8List;
  var respDNS = DNSMessage.parse(respData);
  return respDNS.resource;
}

void main() async {
  var srv = 'dns.pub';
  print("==================> aliyun.com A");
  print(await resolveDOH(srv, 'aliyun.com', DNSMessageType.A));
  print("==================> host.widgets.com TXT");
  print(await resolveDOH(srv, 'host.widgets.com', DNSMessageType.TXT));
  print("==================> www.youtube.com A");
  print(await resolveDOH(srv, 'www.youtube.com', DNSMessageType.A));
}