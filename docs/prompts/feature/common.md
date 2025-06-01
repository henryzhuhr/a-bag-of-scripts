# 通用脚本

## system

### 磁盘使用情况分析

使用 `du` 命令可以查询指定目录下的文件大小，如下

```zsh
% du -h -d 1
137G	./Application Support
1.3G	./pnpm
244M	./Mobile Documents
8.9B	./Group Containers
 95G	./Containers
121M	./Photos
du: ./Saved Application State/com.SITPL.StellarPhotoRecovery.savedState: Permission denied
7.8K	./Caches
# ...
```

我需要过滤出文件/目录大小大于 `500M` 的文件/目录，你还需要跳过 `Permission denied` 的目录，例如过滤后输出为

```zsh
% du -h -d 1
137G	./Application Support
1.3G	./pnpm
 95G	./Containers
# ...
```
