#!/bin/bash
# 向量服务测试脚本
# 用于单独测试weaviate和text2vec-model2vec服务

# 设置颜色输出
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
NC="\033[0m" # No Color

# 创建日志目录
mkdir -p logs

echo -e "${YELLOW}开始测试向量服务...${NC}"

# 检查参数
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
  echo -e "${GREEN}用法:${NC}"
  echo -e "  $0 [选项]"
  echo -e "\n${GREEN}选项:${NC}"
  echo -e "  --text2vec-only    仅测试text2vec-model2vec服务"
  echo -e "  --weaviate-only    仅测试weaviate服务"
  echo -e "  --all              测试所有向量服务（默认）"
  echo -e "  --cleanup          测试后清理所有容器"
  echo -e "  --help, -h         显示此帮助信息"
  exit 0
fi

# 默认参数
TEST_TEXT2VEC=true
TEST_WEAVIATE=true
CLEANUP=false

# 解析参数
for arg in "$@"; do
  case $arg in
    --text2vec-only)
      TEST_TEXT2VEC=true
      TEST_WEAVIATE=false
      ;;
    --weaviate-only)
      TEST_TEXT2VEC=false
      TEST_WEAVIATE=true
      ;;
    --all)
      TEST_TEXT2VEC=true
      TEST_WEAVIATE=true
      ;;
    --cleanup)
      CLEANUP=true
      ;;
  esac
done

# 确保环境文件存在
if [ ! -f .env ]; then
  echo -e "${YELLOW}环境文件不存在，正在从模板创建...${NC}"
  cp .env.template .env
  echo "OPENAI_API_KEY=test_key" >> .env
  echo "HUGGINGFACE_API_KEY=test_key" >> .env
fi

# 测试text2vec-model2vec服务
test_text2vec() {
  echo -e "\n${YELLOW}===== 测试text2vec-model2vec服务 =====${NC}"
  echo -e "${YELLOW}启动text2vec-model2vec服务...${NC}"
  docker compose -f docker-compose.core.yml up -d text2vec-model2vec 2>&1 | tee -a logs/text2vec.log
  
  echo -e "${YELLOW}等待text2vec-model2vec服务就绪...${NC}"
  timeout=60
  counter=0
  
  # 显示容器状态
  echo -e "${YELLOW}检查容器状态:${NC}"
  docker ps -a | grep text2vec-model2vec
  
  # 显示容器日志
  echo -e "${YELLOW}容器日志:${NC}"
  docker logs knowledge-rag-text2vec-model2vec
  
  # 使用8081端口是因为在docker-compose.core.yml中将容器的8080端口映射到了宿主机的8081端口
  # 注意：虽然官方Weaviate文档没有明确说明model2vec有/health端点，但在docker-compose.core.yml中配置了此健康检查端点
  while ! curl -s -f http://localhost:8081/docs > /dev/null; do
    if [ $counter -ge $timeout ]; then
      echo -e "${RED}等待text2vec-model2vec服务超时!${NC}"
      echo -e "${YELLOW}最终容器状态:${NC}"
      docker ps -a | grep text2vec-model2vec
      echo -e "${YELLOW}最终容器日志:${NC}"
      docker logs knowledge-rag-text2vec-model2vec
      return 1
    fi
    echo -n "."
    sleep 1
    counter=$((counter+1))
    
    # 每15秒显示一次容器状态
    if [ $((counter % 15)) -eq 0 ]; then
      echo -e "\n${YELLOW}检查容器状态:${NC}"
      docker ps -a | grep text2vec-model2vec
    fi
  done
  echo -e "\n${GREEN}text2vec-model2vec服务已就绪!${NC}"
  
  echo -e "${YELLOW}测试健康检查端点...${NC}"
  curl -s http://localhost:8081/docs | jq
  
  echo -e "${YELLOW}测试向量化功能...${NC}"
  curl -s -X POST "http://localhost:8081/vectorize" \
    -H "Content-Type: application/json" \
    -d '{"text":"测试文本"}' | jq
  
  echo -e "${GREEN}text2vec-model2vec服务测试完成!${NC}"
  return 0
}

# 测试weaviate服务
test_weaviate() {
  echo -e "\n${YELLOW}===== 测试weaviate服务 =====${NC}"
  
  # 如果没有测试text2vec，需要先启动它
  if [ "$TEST_TEXT2VEC" == "false" ]; then
    echo -e "${YELLOW}启动text2vec-model2vec服务（weaviate依赖）...${NC}"
    docker compose -f docker-compose.core.yml up -d text2vec-model2vec 2>&1 | tee -a logs/weaviate.log
    
    echo -e "${YELLOW}等待text2vec-model2vec服务就绪...${NC}"
    timeout=60
    counter=0
    while ! curl -s -f http://localhost:8081/health > /dev/null; do
      if [ $counter -ge $timeout ]; then
        echo -e "${RED}等待text2vec-model2vec服务超时!${NC}"
        return 1
      fi
      echo -n "."
      sleep 1
      counter=$((counter+1))
    done
    echo -e "\n${GREEN}text2vec-model2vec服务已就绪!${NC}"
  fi
  
  echo -e "${YELLOW}启动weaviate服务...${NC}"
  docker compose -f docker-compose.core.yml up -d weaviate 2>&1 | tee -a logs/weaviate.log
  
  echo -e "${YELLOW}等待weaviate服务就绪...${NC}"
  timeout=120
  counter=0
  while ! curl -s -f http://localhost:8080/v1/.well-known/ready > /dev/null; do
    if [ $counter -ge $timeout ]; then
      echo -e "${RED}等待weaviate服务超时!${NC}"
      return 1
    fi
    echo -n "."
    sleep 1
    counter=$((counter+1))
  done
  echo -e "\n${GREEN}weaviate服务已就绪!${NC}"
  
  echo -e "${YELLOW}测试元数据端点...${NC}"
  curl -s -X GET "http://localhost:8080/v1/meta" | jq
  
  echo -e "${YELLOW}测试创建schema...${NC}"
  curl -s -X POST "http://localhost:8080/v1/schema" \
    -H "Content-Type: application/json" \
    -d '{
      "class": "TestDocument",
      "description": "Test document class",
      "vectorizer": "text2vec-model2vec",
      "properties": [
        {
          "name": "title",
          "dataType": ["text"],
          "description": "Document title"
        },
        {
          "name": "content",
          "dataType": ["text"],
          "description": "Document content"
        }
      ]
    }' | jq
  
  echo -e "${YELLOW}测试添加数据...${NC}"
  curl -s -X POST "http://localhost:8080/v1/objects" \
    -H "Content-Type: application/json" \
    -d '{
      "class": "TestDocument",
      "properties": {
        "title": "测试文档",
        "content": "这是一个测试文档内容"
      }
    }' | jq
  
  echo -e "${GREEN}weaviate服务测试完成!${NC}"
  return 0
}

# 执行测试
if [ "$TEST_TEXT2VEC" == "true" ]; then
  test_text2vec
  TEXT2VEC_RESULT=$?
  if [ $TEXT2VEC_RESULT -ne 0 ]; then
    echo -e "${RED}text2vec-model2vec服务测试失败!${NC}"
  else
    echo -e "${GREEN}text2vec-model2vec服务测试成功!${NC}"
  fi
fi

if [ "$TEST_WEAVIATE" == "true" ]; then
  test_weaviate
  WEAVIATE_RESULT=$?
  if [ $WEAVIATE_RESULT -ne 0 ]; then
    echo -e "${RED}weaviate服务测试失败!${NC}"
  else
    echo -e "${GREEN}weaviate服务测试成功!${NC}"
  fi
fi

# 清理
if [ "$CLEANUP" == "true" ]; then
  echo -e "\n${YELLOW}清理所有容器...${NC}"
  docker compose -f docker-compose.core.yml down -v
  echo -e "${GREEN}清理完成!${NC}"
fi

# 总结
echo -e "\n${YELLOW}===== 测试总结 =====${NC}"
if [ "$TEST_TEXT2VEC" == "true" ]; then
  if [ $TEXT2VEC_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ text2vec-model2vec: 成功${NC}"
  else
    echo -e "${RED}✗ text2vec-model2vec: 失败${NC}"
  fi
fi

if [ "$TEST_WEAVIATE" == "true" ]; then
  if [ $WEAVIATE_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ weaviate: 成功${NC}"
  else
    echo -e "${RED}✗ weaviate: 失败${NC}"
  fi
fi

echo -e "\n${GREEN}测试完成!${NC}"