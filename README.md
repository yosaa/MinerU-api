# MinerU-api

## 项目安装与运行

### 1. 克隆项目并安装依赖

```bash
git clone https://github.com/yosaa/MinerU-api.git
cd MinerU
uv pip install -e .[core] -i https://mirrors.aliyun.com/pypi/simple
````

### 2. 下载模型文件

```bash
mineru-models-download
```

* 根据提示操作
* 下载方式选择：`modelscope`
* 回车继续

### 3. 安装服务端依赖

```bash
pip install -r requirements.txt
```

### 4. 开放防火墙端口（5002）

> 不同系统开放方式不同，请根据自身环境配置。

**Ubuntu:**

```bash
sudo ufw allow 5002/tcp
```

**CentOS (使用 firewalld):**

```bash
sudo firewall-cmd --zone=public --add-port=5002/tcp --permanent
sudo firewall-cmd --reload
```

---

## 接口文档

### 接口 1：批量解析本地文件路径

* **请求方式**：`POST /parse`
* **请求类型**：`application/json`

#### 请求示例

```json
{
  "file_paths": ["/path/to/doc1.docx", "/path/to/doc2.xlsx"],
  "lang": "ch",
  "backend": "pipeline",
  "method": "auto",
  "output_format": "md"
}
```

#### 参数说明

| 参数名            | 类型         | 是否必填 | 默认值          | 描述                                 |
| -------------- | ---------- | ---- | ------------ | ---------------------------------- |
| file\_paths    | List\[str] | ✅ 是  | 无            | 要解析的本地文件路径列表（绝对路径）                 |
| lang           | string     | 否    | `"ch"`       | 语言类型，可选 `"ch"`（中文）或 `"en"`         |
| backend        | string     | 否    | `"pipeline"` | 后端方式，如 `"pipeline"`、`"local"`      |
| method         | string     | 否    | `"auto"`     | 抽取方式，如 `"auto"`、`"qa"`             |
| output\_format | string     | 否    | `"md"`       | 输出格式，支持 `"md"`（Markdown）或 `"html"` |

#### ✅ 响应示例

```json
{
  "doc1": "# 一级标题\n- 抽取内容段落1\n- 抽取内容段落2",
  "doc2": "<h1>标题</h1><p>段落内容</p>"
}
```

* **说明**：键为文档名（去除后缀），值为 Markdown 或 HTML 格式的文本。

---

### 接口 2：上传单个文件进行解析

* **请求方式**：`POST /upload`
* **请求类型**：`multipart/form-data`

#### 表单字段说明

| 参数名            | 类型         | 是否必填 | 默认值          | 描述                                           |
| -------------- | ---------- | ---- | ------------ | -------------------------------------------- |
| file           | UploadFile | ✅ 是  | 无            | 上传的办公文档（支持 `.docx`, `.xlsx`, `.doc`, `.xls`） |
| lang           | string     | 否    | `"ch"`       | 同上                                           |
| backend        | string     | 否    | `"pipeline"` | 同上                                           |
| method         | string     | 否    | `"auto"`     | 同上                                           |
| output\_format | string     | 否    | `"md"`       | 输出格式，支持 `"md"` 或 `"html"`                    |

#### ✅ 响应示例

**Markdown 响应（`output_format=md`）：**

```markdown
# 一级标题
- 抽取内容段落
- 抽取内容段落
```

**HTML 响应（`output_format=html`）：**

```html
<h1>一级标题</h1>
<ul>
  <li>抽取内容段落</li>
</ul>
```

---

## 错误说明

| 错误码 | 错误信息          | 可能原因                   |
| --- | ------------- | ---------------------- |
| 500 | 文档转 PDF 失败    | 未安装 LibreOffice，或文档已损坏 |
| 500 | mineru 命令执行失败 | 未安装 mineru，或命令参数错误等    |
| 422 | 参数校验失败        | 请求体格式错误                |

---

