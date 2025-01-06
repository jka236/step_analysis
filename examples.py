example_list = [
    "public void exampleHardcodedValue() {\n    int value = 100; // Hardcoded value\n    System.out.println(\"The value is: \" + value);\n}",
    "public void unimplementedFeature() {\n    // TODO: Add implementation\n}",
    "public void duplicateMethod() {\n    System.out.println(\"First definition of the method.\");\n}\n\npublic void duplicateMethod() {\n    System.out.println(\"Second definition of the method.\");\n}",
    "public void incorrectCondition() {\n    int x = 5;\n    if (x = 10) { // Should use '==', not '='\n        System.out.println(\"x is equal to 10.\");\n    }\n}",
    "public void exceptionIgnored() {\n    try {\n        riskyOperation();\n    } catch (Exception e) {\n        // Do nothing\n    }\n}",
    "public void exampleHardcodedCredentials() {\n    String username = \"admin\";\n    String password = \"admin123\";\n    authenticate(username, password); // Hardcoded credentials\n}",
    "@Given(\"user logs in\")\npublic void userLogsIn() {\n    System.out.println(\"User logs in with method A.\");\n}\n\n@Given(\"user logs in\")\npublic void userLogsInDuplicate() {\n    System.out.println(\"User logs in with method B.\");\n}",
    "public void inefficientLoop() {\n    for (int i = 0; i < 10; i++) { // Hardcoded loop limit\n        System.out.println(\"Iteration: \" + i);\n    }\n}",
    "public void missingNullCheck(String input) {\n    System.out.println(input.length()); // Potential NullPointerException\n}",
    "public void resourceLeakExample() {\n    FileInputStream fis = new FileInputStream(\"file.txt\"); // No close() method called\n    int data = fis.read();\n    System.out.println(\"Data: \" + data);\n}"
]
