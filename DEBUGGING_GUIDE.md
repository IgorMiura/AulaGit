# 🐛 Guia de Depuração - ClickUp Excel Integration

## 📋 Visão Geral
Este guia ajuda a identificar e resolver problemas comuns na integração entre ClickUp API e Excel/Power BI.

## 🔍 Problemas Comuns e Soluções

### 1. **Erro de Autenticação (401 Unauthorized)**
**Sintomas:** Erro ao fazer requisições para a API
**Causas possíveis:**
- Token expirado ou inválido
- Token sem permissões adequadas

**Soluções:**
```m
// Verificar se o token está correto
Token = "pk_106065011_E8FNOJSJ9XT37RIC2FS7FFIM4BULYG98"

// Adicionar tratamento de erro
Fonte = try Json.Document(
    Web.Contents(Url, [Headers = [Authorization = Token]])
) otherwise [tasks = {}, error = "Authentication failed"]
```

### 2. **Lista Vazia ou Não Encontrada**
**Sintomas:** Nenhuma tarefa retornada
**Causas possíveis:**
- ListId incorreto
- Lista sem tarefas
- Permissões insuficientes

**Soluções:**
```m
// Verificar se ListId está correto
ListId = "901323197844"

// Adicionar log de debug
Tasks = if Record.HasFields(Fonte, "tasks") 
        then Fonte[tasks] 
        else 
            let
                ErrorMsg = if Record.HasFields(Fonte, "err") 
                          then Fonte[err] 
                          else "No tasks field found"
            in
                error ErrorMsg
```

### 3. **Problemas de Hierarquia**
**Sintomas:** Tarefas fora de ordem ou hierarquia incorreta
**Causas possíveis:**
- Referências circulares entre tarefas
- IDs de parent inconsistentes

**Soluções:**
```m
// Adicionar validação de referências circulares
ValidateHierarchy = (tasks as list) as list =>
    let
        // Verificar se há referências circulares
        TaskIds = List.Transform(tasks, each Text.From([id])),
        ParentIds = List.Transform(tasks, each 
            if [parent] = null then "" else Text.From([parent])
        ),
        
        // Filtrar apenas parents válidos
        ValidTasks = List.Select(tasks, each
            [parent] = null or List.Contains(TaskIds, Text.From([parent]))
        )
    in
        ValidTasks
```

### 4. **Performance Lenta**
**Sintomas:** Consulta demora muito para executar
**Causas possíveis:**
- Muitas páginas de dados
- Recursão excessiva

**Soluções:**
```m
// Adicionar limite de páginas
MaxPages = 50,
Pages = List.Generate(
    () => [Page = 0, Tasks = GetPage(0), Count = 0],
    each List.Count([Tasks]) > 0 and [Count] < MaxPages,
    each [
        Page = [Page] + 1,
        Tasks = GetPage([Page] + 1),
        Count = [Count] + 1
    ],
    each [Tasks]
)
```

### 5. **Campos Ausentes**
**Sintomas:** Erro ao expandir colunas
**Causas possíveis:**
- Nem todas as tarefas têm os mesmos campos
- Campos nulos ou vazios

**Soluções:**
```m
// Expandir apenas campos que existem em todas as tarefas
CommonFields = if List.Count(OrganizedTasks) = 0 then {} else
    let
        AllFieldNames = List.Transform(OrganizedTasks, each Record.FieldNames(_)),
        CommonFieldsList = List.Accumulate(
            AllFieldNames,
            if List.Count(AllFieldNames) > 0 then AllFieldNames{0} else {},
            (state, current) => List.Intersect({state, current})
        )
    in
        CommonFieldsList,

ExpandedTable = if List.Count(OrganizedTasks) = 0 then
    TasksTable
else
    Table.ExpandRecordColumn(TasksTable, "Task", CommonFields, CommonFields)
```

## 🔧 Melhorias Sugeridas

### 1. **Configuração Flexível**
```m
// Mover configurações para parâmetros
(Token as text, ListId as text, MaxPages as number) as table =>
let
    // ... resto do código
```

### 2. **Tratamento de Erros Robusto**
```m
// Adicionar try-catch em pontos críticos
SafeGetPage = (page as number) as list =>
    try GetPage(page)
    otherwise 
        let
            ErrorRecord = [
                id = "error_" & Text.From(page),
                name = "Erro ao carregar página " & Text.From(page),
                status = [status = "error"]
            ]
        in
            {ErrorRecord}
```

### 3. **Cache de Dados**
```m
// Implementar cache simples para evitar requisições desnecessárias
CachedData = if Duration.TotalMinutes(DateTime.LocalNow() - LastUpdate) < 5
             then StoredData
             else FreshData
```

### 4. **Logging e Debug**
```m
// Adicionar informações de debug
DebugInfo = [
    TotalTasks = List.Count(AllTasks),
    MainTasks = List.Count(MainTasks),
    SubTasks = List.Count(SubTasks),
    MaxLevel = List.Max(List.Transform(FinalTable[Task_Level], each 
        Number.FromText(Text.BetweenDelimiters(_, "Nível ", " -"))
    ))
]
```

## 🧪 Testes Recomendados

### 1. **Teste com Lista Vazia**
- Usar ListId de uma lista sem tarefas
- Verificar se retorna tabela vazia sem erros

### 2. **Teste com Hierarquia Complexa**
- Criar tarefas com 5+ níveis de profundidade
- Verificar se a organização está correta

### 3. **Teste de Performance**
- Medir tempo de execução com diferentes volumes de dados
- Identificar gargalos

### 4. **Teste de Conectividade**
- Simular falhas de rede
- Verificar comportamento com timeouts

## 📊 Monitoramento

### Métricas Importantes:
- Tempo de execução total
- Número de requisições à API
- Taxa de erro por página
- Profundidade máxima da hierarquia

### Alertas Sugeridos:
- Tempo de execução > 5 minutos
- Taxa de erro > 10%
- Mais de 100 páginas de dados

## 🚀 Próximos Passos

1. **Implementar configuração por parâmetros**
2. **Adicionar cache inteligente**
3. **Criar versão otimizada para grandes volumes**
4. **Implementar retry automático para falhas temporárias**
5. **Adicionar suporte a filtros personalizados**

---

**💡 Dica:** Sempre teste em ambiente de desenvolvimento antes de aplicar em produção!
