# Pipeline SQS para S3 com AWS Lambda

## Visão Geral
Este projeto implementa um pipeline serverless para processar mensagens do Amazon SQS e armazená-las no Amazon S3, utilizando AWS Lambda. O sistema é organizado com uma estrutura de pastas baseada em data (YYYY/MM/DD) para melhor gerenciamento dos arquivos.

## Funcionalidades Principais
- Processamento em lote de mensagens SQS
- Organização automática em pastas por data
- Processamento paralelo de mensagens
- Tratamento robusto de erros
- Relatório detalhado de falhas em lote
- Metadados completos para cada arquivo

## Arquitetura

### Diagrama do Sistema
```
                   ┌─────────────┐
                   │    SQS      │
                   │   Queue     │
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Lambda    │
                   │  Function   │
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │     S3      │
                   │   Bucket    │
                   └─────────────┘
```

### Componentes
1. **AWS Lambda (lambda_function.py)**
   - Processa mensagens em lote
   - Organiza arquivos por data
   - Gerencia metadados
   - Trata erros e falhas
   - Processamento paralelo com ThreadPoolExecutor

2. **Infraestrutura Terraform (main.tf)**
   - Configuração da função Lambda
   - Definição da fila SQS
   - Bucket S3
   - Políticas IAM
   - Mapeamento de eventos

3. **Ambiente Local (docker-compose.yml)**
   - LocalStack para simulação AWS
   - Ambiente Docker isolado
   - Configuração de serviços

## Estrutura de Armazenamento
```
s3://bucket-name/
    └── YYYY/               # Ano
        └── MM/            # Mês
            └── DD/        # Dia
                └── HHMMSS_microseconds_messageId.json
```

## Metadados
Cada arquivo armazenado inclui:
- ID da mensagem
- Timestamp de processamento
- ID da requisição
- Ano/Mês/Dia
- Atributos da mensagem
- Detalhes do processamento

## Configuração do Ambiente

### Pré-requisitos
- Python 3.9+
- Docker Desktop
- Terraform 1.5.0+
- LocalStack (para desenvolvimento local)
- AWS CLI (opcional)

### Instalação
1. Clone o repositório
2. Configure o ambiente Docker:
   ```bash
   docker-compose up -d
   ```
3. Configure o LocalStack ou credenciais AWS
4. Aplique a infraestrutura:
   ```bash
   docker-compose run --rm terraform init
   docker-compose run --rm terraform apply
   ```

## Testes
O projeto inclui testes unitários abrangentes:

```bash
python -m pytest -v --cov=.
```

### Cobertura de Testes
- Geração de caminhos
- Processamento de mensagens
- Tratamento de erros
- Processamento em lote
- Validação de metadados

## Configurações

### Lambda
- Memória: 128 MB
- Timeout: 3 segundos
- Tamanho do Lote: 10 mensagens
- Lotes Concorrentes: 2

### SQS
- Nome da Fila: incoming-messages-queue
- Processamento em Lote: Habilitado
- Relatório de Falhas: Habilitado

### S3
- Nome do Bucket: sqs-messages-bucket
- Organização: Por data (YYYY/MM/DD)
- Force Destroy: true

### Variáveis de Ambiente
```env
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=us-east-1
AWS_ENDPOINT_URL=http://localhost:4566
SQS_QUEUE_NAME=incoming-messages-queue
S3_BUCKET_NAME=sqs-messages-bucket
```

## Segurança
- Permissões IAM mínimas necessárias
- Sem dados sensíveis no código
- Logging seguro de informações
- Tratamento adequado de erros
- Credenciais de teste apenas para desenvolvimento local

## Logs e Monitoramento
- Logs detalhados de processamento
- Rastreamento de mensagens
- Métricas de sucesso/falha
- Informações de lote
- Relatórios de processamento em paralelo

## Uso

### Envio de Mensagens
```bash
docker-compose run --rm message-sender
```

### Verificação de Resultados
1. Acesse o bucket S3
2. Navegue pela estrutura de pastas (YYYY/MM/DD)
3. Verifique os arquivos JSON e metadados

## Limitações Conhecidas
- Timeout pode ser insuficiente para lotes grandes
- Sem implementação de DLQ
- Mecanismos limitados de recuperação de erros

## Ciclo de Desenvolvimento
1. Desenvolvimento local com LocalStack
2. Testes unitários
3. Validação de infraestrutura
4. Deploy para produção

## Estrutura do Projeto
```
lambda_sqs_to_s3/
├── lambda_function.py     # Função Lambda
├── main.tf               # Configuração Terraform
├── test_lambda_function.py # Suite de testes
├── docker-compose.yml    # Serviços locais
└── .gitignore           # Regras do Git
```

## Referências
- [Documentação AWS Lambda](https://docs.aws.amazon.com/lambda)
- [Documentação AWS SQS](https://docs.aws.amazon.com/sqs)
- [Documentação Terraform](https://www.terraform.io/docs)

## Contribuição
1. Fork o projeto
2. Crie sua branch de feature
3. Commit suas alterações
4. Push para a branch
5. Abra um Pull Request

## Licença
Este projeto está sob a licença MIT.
