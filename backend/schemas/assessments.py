from pydantic import BaseModel, Field

class ExplanationItem(BaseModel):
    feature: str
    contribution: float
    direction: str


class DiabetesInput(BaseModel):
    Pregnancies: float = Field(..., ge=0, le=20)
    Glucose: float = Field(..., ge=0, le=300)
    BloodPressure: float = Field(..., ge=0, le=200)
    SkinThickness: float = Field(..., ge=0, le=150)
    Insulin: float = Field(..., ge=0, le=1000)
    BMI: float = Field(..., ge=0, le=80)
    DiabetesPedigreeFunction: float = Field(..., ge=0, le=3)
    Age: float = Field(..., ge=1, le=120)



class HeartDiseaseInput(BaseModel):
    age: float = Field(..., ge=1, le=120)
    sex: float = Field(..., ge=0, le=1)
    cp: float = Field(..., ge=1, le=4)
    trestbps: float = Field(..., ge=50, le=250)
    chol: float = Field(..., ge=50, le=700)
    fbs: float = Field(..., ge=0, le=1)
    restecg: float = Field(..., ge=0, le=2)
    thalach: float = Field(..., ge=50, le=250)
    exang: float = Field(..., ge=0, le=1)
    oldpeak: float = Field(..., ge=-5, le=10)
    slope: float = Field(..., ge=1, le=3)
    ca: float = Field(..., ge=0, le=3)
    thal: float = Field(..., ge=3, le=7)



class DiabetesResponse(BaseModel):
    prediction: int
    result: str
    probability: float
    threshold: float
    model: str
    model_version: str
    explanation: list[ExplanationItem]



class HeartDiseaseResponse(BaseModel):
    prediction: int
    result: str
    probability: float
    threshold: float
    model: str
    model_version: str
    explanation: list[ExplanationItem]
