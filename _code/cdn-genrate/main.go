package main

import (
	"crypto/sha256"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"

	"hash/fnv"

	"golang.org/x/crypto/chacha20"
)

func sizeFromURI(uri string, minSize, maxSize int) int {
	h := fnv.New64a()
	h.Write([]byte(uri))
	val := h.Sum64()
	diff := maxSize - minSize + 1
	return minSize + int(val%uint64(diff))
}

type HttpRange struct {
	Start, End int64
}

// ParseRange 解析 Range 头，只支持形如 bytes=start-end 的情况
func ParseRange(s string, size int64) ([]HttpRange, error) {
	if s == "" || !strings.HasPrefix(s, "bytes=") {
		return nil, fmt.Errorf("invalid range header")
	}
	rangesSpec := strings.TrimPrefix(s, "bytes=")
	parts := strings.SplitN(rangesSpec, "-", 2)
	if len(parts) != 2 {
		return nil, fmt.Errorf("invalid range format")
	}

	var start, end int64
	var err error

	if parts[0] == "" { // "-500" => 最后 500 字节
		n, err := strconv.ParseInt(parts[1], 10, 64)
		if err != nil {
			return nil, err
		}
		if n > size {
			n = size
		}
		start = size - n
		end = size - 1
	} else {
		start, err = strconv.ParseInt(parts[0], 10, 64)
		if err != nil {
			return nil, err
		}
		if parts[1] == "" { // "500-" => 从500到结尾
			end = size - 1
		} else {
			end, err = strconv.ParseInt(parts[1], 10, 64)
			if err != nil {
				return nil, err
			}
		}
		if start > end || start < 0 || end >= size {
			return nil, fmt.Errorf("invalid range values")
		}
	}
	return []HttpRange{{Start: start, End: end}}, nil
}

// SeededStream 结构体，支持随机访问
type SeededStream struct {
	key   [32]byte
	nonce [12]byte
}

// NewSeededStream 初始化
func NewSeededStream(seed []byte) *SeededStream {
	var s SeededStream
	keyHash := sha256.Sum256(seed)
	copy(s.key[:], keyHash[:32])

	nonceHash := sha256.Sum256(append(seed, []byte("nonce")...))
	copy(s.nonce[:], nonceHash[:12])

	return &s
}

// Bytes 返回 [offset, offset+n) 区间的伪随机字节
func (s *SeededStream) Bytes(offset, n int) []byte {
	block := uint32(offset / 64)
	startInBlock := offset % 64

	cipher, err := chacha20.NewUnauthenticatedCipher(s.key[:], s.nonce[:])
	if err != nil {
		log.Fatal(err)
	}
	cipher.SetCounter(block)

	buf := make([]byte, n+startInBlock)
	cipher.XORKeyStream(buf, buf)
	return buf[startInBlock:]
}

// StreamWrite 边生成边写到 w，避免占用过多内存
func (s *SeededStream) StreamWrite(w http.ResponseWriter, offset, n int) error {
	const chunkSize = 64 * 1024 // 64KB
	sent := 0
	for sent < n {
		toGen := chunkSize
		if n-sent < toGen {
			toGen = n - sent
		}
		data := s.Bytes(offset+sent, toGen)
		if _, err := w.Write(data); err != nil {
			return err
		}
		sent += toGen
	}
	return nil
}

func main() {
	if len(os.Args) < 4 {
		fmt.Println("用法: ./main <端口> <最小文件大小> <最大文件大小>")
		return
	}
	port := os.Args[1]
	minSize, err1 := strconv.Atoi(os.Args[2])
	maxSize, err2 := strconv.Atoi(os.Args[3])
	if err1 != nil || err2 != nil || minSize <= 0 || maxSize < minSize {
		fmt.Println("文件大小参数错误: 最小文件大小必须为正整数，最大文件大小必须 >= 最小文件大小")
		return
	}

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		uri := r.URL.Path
		seed := []byte(uri)
		stream := NewSeededStream(seed)
		size := sizeFromURI(uri, minSize, maxSize)

		w.Header().Set("Content-Type", "application/octet-stream")

		// 支持 Range 请求
		ranges, err := ParseRange(r.Header.Get("Range"), int64(size))
		if err == nil && len(ranges) > 0 {
			// 这里只处理第一个 range
			rng := ranges[0]
			start, end := int(rng.Start), int(rng.End)
			length := end - start + 1

			w.Header().Set("Content-Range", fmt.Sprintf("bytes %d-%d/%d", start, end, size))
			w.Header().Set("Content-Length", strconv.Itoa(length))
			w.WriteHeader(http.StatusPartialContent)
			_ = stream.StreamWrite(w, start, length)
			log.Printf("200 PARTIAL %s range=%d-%d size=%d", uri, start, end, size)
			return
		}

		// 无 Range 请求，完整文件
		w.Header().Set("Content-Length", strconv.Itoa(size))
		w.WriteHeader(http.StatusOK)
		_ = stream.StreamWrite(w, 0, size)
		log.Printf("200 FULL %s size=%d", uri, size)
	})

	fmt.Printf("监听端口: %s, 文件大小范围: [%d, %d]\n", port, minSize, maxSize)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
