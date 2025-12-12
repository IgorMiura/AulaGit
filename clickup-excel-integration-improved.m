// ClickUp API Integration for Excel/Power BI - VERSÃO MELHORADA
// Integração da API do ClickUp para Excel/Power BI - COM TRATAMENTO DE ERROS
// 
// Esta versão inclui melhorias de performance, tratamento de erros e debugging
//
// Autor: Igor Miura
// Data: 2024-12-12
// Versão: 2.0 - Melhorada

// FUNÇÃO PRINCIPAL - PODE SER PARAMETRIZADA
(optional Token as text, optional ListId as text, optional MaxPages as number) as table =>
let
    // CONFIGURAÇÕES PADRÃO (podem ser sobrescritas pelos parâmetros)
    DefaultToken = "pk_106065011_E8FNOJSJ9XT37RIC2FS7FFIM4BULYG98",
    DefaultListId = "901323197844",
    DefaultMaxPages = 50,
    
    // USAR PARÂMETROS OU VALORES PADRÃO
    FinalToken = if Token = null then DefaultToken else Token,
    FinalListId = if ListId = null then DefaultListId else ListId,
    FinalMaxPages = if MaxPages = null then DefaultMaxPages else MaxPages,

    // FUNÇÃO SEGURA PARA BUSCAR UMA PÁGINA DE TASKS
    SafeGetPage = (page as number) as record =>
        let
            Url = 
                "https://api.clickup.com/api/v2/list/" 
                & FinalListId 
                & "/task?include_closed=true&subtasks=true&include_markdown_description=false&page=" 
                & Number.ToText(page),

            Result = try
                let
                    Response = Web.Contents(
                        Url,
                        [
                            Headers = [Authorization = FinalToken],
                            Timeout = #duration(0, 0, 1, 0) // 1 minuto timeout
                        ]
                    ),
                    JsonData = Json.Document(Response),
                    Tasks = if Record.HasFields(JsonData, "tasks") 
                           then JsonData[tasks] 
                           else {}
                in
                    [Success = true, Tasks = Tasks, Error = null, Page = page]
            otherwise
                [
                    Success = false, 
                    Tasks = {}, 
                    Error = "Erro ao carregar página " & Text.From(page), 
                    Page = page
                ]
        in
            Result,

    // GERA AS PÁGINAS COM LIMITE E TRATAMENTO DE ERRO
    Pages =
        List.Generate(
            () => [
                Page = 0, 
                Result = SafeGetPage(0),
                Count = 0,
                HasMore = true
            ],
            each [HasMore] and [Count] < FinalMaxPages,
            each 
                let
                    NextPage = [Page] + 1,
                    NextResult = SafeGetPage(NextPage),
                    HasTasks = NextResult[Success] and List.Count(NextResult[Tasks]) > 0
                in
                [
                    Page = NextPage,
                    Result = NextResult,
                    Count = [Count] + 1,
                    HasMore = HasTasks
                ],
            each [Result]
        ),

    // SEPARAR RESULTADOS VÁLIDOS DOS ERROS
    ValidPages = List.Select(Pages, each [Success] = true),
    ErrorPages = List.Select(Pages, each [Success] = false),
    
    // JUNTA TODAS AS LISTAS DE TASKS EM UMA SÓ
    AllTasks = List.Combine(List.Transform(ValidPages, each [Tasks])),

    // VALIDAÇÃO DE HIERARQUIA - EVITA REFERÊNCIAS CIRCULARES
    ValidateHierarchy = (tasks as list) as list =>
        let
            TaskIds = List.Transform(tasks, each Text.From([id])),
            ValidTasks = List.Select(tasks, each
                [parent] = null or 
                [parent] = "" or 
                List.Contains(TaskIds, Text.From([parent]))
            )
        in
            ValidTasks,

    // APLICAR VALIDAÇÃO
    ValidatedTasks = if List.Count(AllTasks) = 0 then {} else ValidateHierarchy(AllTasks),

    // FUNÇÃO RECURSIVA MELHORADA PARA ORGANIZAR HIERARQUIA
    OrganizeTasksHierarchy = (tasks as list) as list =>
        let
            // Separar tarefas principais (sem parent) das subtarefas
            MainTasks = List.Select(tasks, each 
                try [parent] = null or [parent] = "" 
                otherwise true
            ),
            
            SubTasks = List.Select(tasks, each 
                try [parent] <> null and [parent] <> "" 
                otherwise false
            ),
            
            // Função para encontrar filhos de uma tarefa (com limite de profundidade)
            GetChildren = (parentId as text, remainingTasks as list, depth as number) as list =>
                if depth > 10 then {} // Limite de profundidade para evitar loops infinitos
                else
                    let
                        DirectChildren = List.Select(remainingTasks, each 
                            try Text.From([parent]) = parentId 
                            otherwise false
                        ),
                        
                        RemainingAfterDirectChildren = List.Select(remainingTasks, each 
                            try Text.From([parent]) <> parentId 
                            otherwise true
                        ),
                        
                        // Para cada filho direto, buscar seus filhos recursivamente
                        ChildrenWithSubChildren = List.Transform(DirectChildren, each 
                            let
                                CurrentTask = _,
                                TaskId = Text.From([id]),
                                TaskChildren = @GetChildren(TaskId, RemainingAfterDirectChildren, depth + 1)
                            in
                                {CurrentTask} & TaskChildren
                        ),
                        
                        FlattenedChildren = List.Combine(ChildrenWithSubChildren)
                    in
                        FlattenedChildren,
            
            // Organizar cada tarefa principal com seus filhos
            OrganizedTasks = List.Transform(MainTasks, each
                let
                    CurrentTask = _,
                    TaskId = Text.From([id]),
                    TaskChildren = GetChildren(TaskId, SubTasks, 0)
                in
                    {CurrentTask} & TaskChildren
            ),
            
            FinalOrganizedTasks = List.Combine(OrganizedTasks)
        in
            FinalOrganizedTasks,

    // ORGANIZAR AS TAREFAS EM HIERARQUIA
    OrganizedTasks = if List.Count(ValidatedTasks) = 0 then {} else OrganizeTasksHierarchy(ValidatedTasks),

    // CONVERTER PARA TABELA COM TRATAMENTO DE ERRO
    TasksTable = if List.Count(OrganizedTasks) = 0 then
        #table({"Info"}, {{"Nenhuma tarefa encontrada"}})
    else
        Table.FromList(OrganizedTasks, Splitter.SplitByNothing(), {"Task"}, null, ExtraValues.Error),

    // EXPANDIR CAMPOS DA TASK COM CAMPOS COMUNS
    ExpandedTable = if List.Count(OrganizedTasks) = 0 then
        TasksTable
    else
        let
            // Encontrar campos comuns a todas as tarefas
            AllFieldNames = List.Transform(OrganizedTasks, each Record.FieldNames(_)),
            CommonFields = if List.Count(AllFieldNames) > 0 then
                List.Accumulate(
                    List.Skip(AllFieldNames, 1),
                    AllFieldNames{0},
                    (state, current) => List.Intersect({state, current})
                )
            else {},
            
            // Expandir apenas campos comuns
            Expanded = if List.Count(CommonFields) > 0 then
                Table.ExpandRecordColumn(TasksTable, "Task", CommonFields, CommonFields)
            else
                TasksTable
        in
            Expanded,

    // ADICIONAR COLUNAS DE NÍVEL E NOME DA TAREFA PAI (MELHORADO)
    FinalTable = if List.Count(OrganizedTasks) = 0 then
        ExpandedTable
    else
        let
            // Adicionar coluna de nível baseada na posição na hierarquia
            WithLevel = Table.AddColumn(ExpandedTable, "Task_Level", each
                let
                    CurrentId = Text.From([id]),
                    TopLevelParentId = if [top_level_parent] = null then CurrentId else Text.From([top_level_parent]),
                    
                    // Contar quantas linhas existem entre top_level_parent e a task atual
                    CurrentRowIndex = Table.PositionOf(ExpandedTable, _, MissingField.UseNull),
                    TopLevelRowIndex = try
                        Table.PositionOf(
                            ExpandedTable, 
                            Table.SelectRows(ExpandedTable, each Text.From([id]) = TopLevelParentId){0},
                            MissingField.UseNull
                        )
                    otherwise CurrentRowIndex,
                    
                    Level = if CurrentRowIndex = null or TopLevelRowIndex = null then 0
                           else CurrentRowIndex - TopLevelRowIndex,
                    
                    LevelText = if Level = 0 then "Nível 0 - Tarefa Principal"
                           else if Level = 1 then "Nível 1 - Subtarefa"
                           else if Level = 2 then "Nível 2 - Subtarefa da Subtarefa"
                           else if Level = 3 then "Nível 3 - Subtarefa Nível 3"
                           else if Level = 4 then "Nível 4 - Subtarefa Nível 4"
                           else if Level = 5 then "Nível 5 - Subtarefa Nível 5"
                           else "Nível " & Text.From(Level) & " - Subtarefa Avançada"
                in
                    LevelText
            ),
            
            // Adicionar coluna com nome da tarefa pai
            WithParentName = Table.AddColumn(WithLevel, "Parent_Task_Name", each
                if [parent] = null or [parent] = "" then ""
                else
                    let
                        ParentId = Text.From([parent]),
                        ParentRow = try
                            Table.SelectRows(WithLevel, each Text.From([id]) = ParentId){0}
                        otherwise null,
                        ParentName = if ParentRow = null then "Parent não encontrado" else ParentRow[name]
                    in
                        ParentName
            ),
            
            // Adicionar informações de debug
            WithDebugInfo = Table.AddColumn(WithParentName, "Debug_Info", each
                [
                    TotalTasks = List.Count(AllTasks),
                    ValidatedTasks = List.Count(ValidatedTasks),
                    OrganizedTasks = List.Count(OrganizedTasks),
                    ErrorPages = List.Count(ErrorPages),
                    PagesLoaded = List.Count(ValidPages)
                ]
            )
        in
            WithDebugInfo
in
    FinalTable
