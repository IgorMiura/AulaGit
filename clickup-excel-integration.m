// ClickUp API Integration for Excel/Power BI
// Integração da API do ClickUp para Excel/Power BI
// 
// Esta função busca tarefas da API do ClickUp e organiza em estrutura hierárquica
// para uso em Excel ou Power BI
//
// Autor: Igor Miura
// Data: 2024-12-12

let
    // CONFIGURAÇÕES
    Token  = "pk_106065011_E8FNOJSJ9XT37RIC2FS7FFIM4BULYG98",
    ListId = "901323197844",

    // FUNÇÃO QUE BUSCA UMA PÁGINA DE TASKS E RETORNA UMA LISTA
    GetPage = (page as number) as list =>
        let
            Url = 
                "https://api.clickup.com/api/v2/list/" 
                & ListId 
                & "/task?include_closed=true&subtasks=true&include_markdown_description=false&page=" 
                & Number.ToText(page),

            Fonte = Json.Document(
                Web.Contents(
                    Url,
                    [
                        Headers = [Authorization = Token]
                    ]
                )
            ),

            Tasks = 
                if Record.HasFields(Fonte, "tasks") 
                then Fonte[tasks] 
                else {}
        in
            Tasks,

    // GERA AS PÁGINAS ENQUANTO VIEREM TASKS
    Pages =
        List.Generate(
            () => [Page = 0, Tasks = GetPage(0)],
            each List.Count([Tasks]) > 0,
            each [
                Page = [Page] + 1,
                Tasks = GetPage([Page] + 1)
            ],
            each [Tasks]
        ),

    // JUNTA TODAS AS LISTAS DE TASKS EM UMA SÓ
    AllTasks = List.Combine(Pages),

    // FUNÇÃO RECURSIVA PARA ORGANIZAR HIERARQUIA
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
            
            // Função para encontrar filhos de uma tarefa
            GetChildren = (parentId as text, remainingTasks as list) as list =>
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
                            TaskChildren = @GetChildren(TaskId, RemainingAfterDirectChildren)
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
                    TaskChildren = GetChildren(TaskId, SubTasks)
                in
                    {CurrentTask} & TaskChildren
            ),
            
            FinalOrganizedTasks = List.Combine(OrganizedTasks)
        in
            FinalOrganizedTasks,

    // ORGANIZAR AS TAREFAS EM HIERARQUIA
    OrganizedTasks = if List.Count(AllTasks) = 0 then {} else OrganizeTasksHierarchy(AllTasks),

    // CONVERTER PARA TABELA
    TasksTable = if List.Count(OrganizedTasks) = 0 then
        Table.FromList({}, Splitter.SplitByNothing(), {"Task"}, null, ExtraValues.Error)
    else
        Table.FromList(OrganizedTasks, Splitter.SplitByNothing(), {"Task"}, null, ExtraValues.Error),

    // EXPANDIR CAMPOS DA TASK
    ExpandedTable = if List.Count(OrganizedTasks) = 0 then
        TasksTable
    else
        Table.ExpandRecordColumn(
            TasksTable,
            "Task",
            Record.FieldNames(OrganizedTasks{0}),
            Record.FieldNames(OrganizedTasks{0})
        ),

    // ADICIONAR COLUNAS DE NÍVEL E NOME DA TAREFA PAI
    FinalTable = if List.Count(OrganizedTasks) = 0 then
        ExpandedTable
    else
        let
            // Adicionar coluna de nível baseada na distância do top_level_parent
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
                           else if Level = 6 then "Nível 6 - Subtarefa Nível 6"
                           else if Level = 7 then "Nível 7 - Subtarefa Nível 7"
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
                        ParentName = if ParentRow = null then "" else ParentRow[name]
                    in
                        ParentName
            )
        in
            WithParentName
in
    FinalTable
