import json
from typing import Dict, List
from dataclasses import dataclass
import glob
from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser

from pydantic import BaseModel, Field


class StepAnalysis(BaseModel):
    step_text: str = Field(description="The step definition being analyzed")
    issues: List[str] = Field(description="List of identified issues")
    line_number: List[int] = Field(description="List of line numbers of identified issues. This should match with the number of issues")
    suggestions: List[str] = Field(description="Improvement suggestions. This should match with the number of issues")
    confidence: float = Field(description="Confidence score of the analysis")


class ContextCollector:
    def __init__(self, project_root: str):
        self.project_root = project_root

    def collect_features(self) -> List[str]:
        """Collect all feature file contents for context"""
        feature_files = glob.glob(f"{self.project_root}/**/*.feature", recursive=True)
        return [self._read_file(f) for f in feature_files]

    def collect_step_definitions(self) -> List[str]:
        """Collect all step definition file contents"""
        # Adjust patterns based on your project's structure and file extensions
        patterns = [
            "**/steps/*.java",
        ]
        step_files = []
        for pattern in patterns:
            step_files.extend(glob.glob(f"{self.project_root}/{pattern}", recursive=True))
        return [self._read_file(f) for f in step_files]

    def collect_implementation_code(self) -> List[str]:
        """Collect relevant implementation code"""
        # Adjust patterns based on your project structure
        impl_patterns = [
            "**/*.java",
            # Add patterns for other languages as needed
        ]
        impl_files = []
        for pattern in impl_patterns:
            impl_files.extend(glob.glob(f"{self.project_root}/{pattern}", recursive=True))
        return [self._read_file(f) for f in impl_files]

    @staticmethod
    def _read_file(path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading {path}: {e}")
            return ""


class StepDefinitionAnalyzer:
    def __init__(self, model="gpt-4o-mini"):
        self.llm = ChatOpenAI(temperature=0, model=model)
        self.parser = PydanticOutputParser(pydantic_object=StepAnalysis)
        self.analysis_chain = self._create_analysis_chain()

    def _create_analysis_chain(self) -> PromptTemplate:
        template = """
        Analyze this specific step definition in the context of the entire test suite to detect BOGUS tests.
        Please only report important warning.

        A bogus test could include the following characteristics:

        Incomplete Tests:
        Steps in the feature file that are missing corresponding step definitions.
        Steps with placeholders instead of real values (e.g., <some_value>).
        
        Ambiguities and Errors:
        Steps with ambiguous or poorly defined behavior.
        Multiple step definitions match the same step (causing ambiguity errors).
        
        Logical Contradictions:
        Steps that contradict each other (e.g., two conflicting "Given" steps).
        Steps with inconsistent parameter usage (e.g., mismatched variable names).
        
        Redundant or Duplicate Tests:
        Scenarios that are identical or almost identical to others.
        Steps that repeat unnecessarily within a single scenario.
        
        Unused or Undefined Steps:
        Step definitions that are never referenced in any feature file.
        Steps in feature files that do not have corresponding step definitions.
        
        Lack of Assertions:
        Scenarios missing validation steps (e.g., no "Then" step or missing meaningful assertions).
        
        Overly Broad Scenarios:
        Scenarios that lack specificity or clear expected outcomes.

        Step Definition to Analyze:
        {target_step}

        Context - Feature Files:
        {feature_context}

        Context - Other Step Definitions:
        {step_context}

        Return your analysis in the following JSON format:
        {format_instructions}
        """

        return PromptTemplate(
            input_variables=["target_step", "feature_context", "step_context"],
            template=template,
            partial_variables={"format_instructions": self.parser.get_format_instructions()},
            output_parser=self.parser
        )

    def analyze_step(self, target_step: str, project_root: str) -> Dict:
        """
        Analyze a specific step definition using the entire codebase as context
        """
        # Collect context
        collector = ContextCollector(project_root)
        features = collector.collect_features()
        step_defs = collector.collect_step_definitions()
        inputs = {
            "target_step" : target_step, 
            "feature_context" : "\n\n".join(features), 
            "step_context" : "\n\n".join(step_defs), 
        }
        # Run analysis
        chain = self.analysis_chain | self.llm | StrOutputParser()
        result = chain.invoke(inputs)

        # Parse and return results
        return self.parser.parse(result).model_dump_json(indent = 2)


# Example usage
def main():
    load_dotenv()

    # Example step definition to analyze
    target_step = """
    @Then("the response status code of getting an account should be {int}")
    public void theResponseStatusCodeOfGettingAnAccountShouldBe(int statusCode) {
    }
    """

    analyzer = StepDefinitionAnalyzer()
    result = analyzer.analyze_step(target_step=target_step, project_root="./bogusdetector")

    print(result)


if __name__ == "__main__":
    main()


