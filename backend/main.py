from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from .database import get_db_connection
import json

from .core.config import CORS_ORIGINS
from .core.security import (
    create_access_token,
    get_current_user,
    pwd_context,
)

from .schemas.auth import (
    RegisterInput,
    LoginInput,
    ChangePasswordInput,
)

from .schemas.users import (
    UpdateProfileInput,
)

from .schemas.assessments import (
    ExplanationItem,
    DiabetesInput,
    HeartDiseaseInput,
    DiabetesResponse,
    HeartDiseaseResponse,
)

from .repositories.users import (
    get_user_by_email,
    get_user_by_id,
    create_user,
    email_exists_for_other_user,
    update_user,
    update_password,
    get_user_by_id_with_password,
)

from .repositories.assessments import (
    get_user_history,
    get_prediction_by_id,
    save_prediction,
)

from ml.src.predict_heart_disease import predict_heart_disease
from ml.shap.shap_heart import explain_prediction

from ml.src.predict_diabetes import predict_diabetes
from ml.shap.shap_diabetes import explain_diabetes_prediction

from .database import create_tables

app = FastAPI(title="GeneCare AI APP")

create_tables()


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post(
    "/predict/heart-disease",
    response_model=HeartDiseaseResponse
)
def predict_heart(
    data: HeartDiseaseInput,
    user_id: int = Depends(get_current_user)
):

    patient_data = data.model_dump()

    result = predict_heart_disease(patient_data)

    if result["prediction"] == 1:
        result["result"] = "Higher Heart-Disease risk pattern estimated"
    else:
        result["result"] = "Lower Heart-Disease risk pattern estimated"

    result["explanation"] = explain_prediction(
        patient_data
    )

    try:
        save_prediction(
            user_id=user_id,
            disease="Heart Disease",
            prediction=result["prediction"],
            result=result["result"],
            probability=result["probability"],
            input_data=json.dumps(patient_data),
            explanation=json.dumps(result["explanation"]),
            model_name=result["model"],
            model_version=result["model_version"],
        )

    except Exception as e:
        print(f"Database error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Prediction was successful, but could not be saved."
        )

    return result

@app.post(
    "/predict/diabetes",
    response_model=DiabetesResponse
)
def predict_diabetes_endpoint(
    data: DiabetesInput,
    user_id: int = Depends(get_current_user)
):

    patient_data = data.model_dump()

    result = predict_diabetes(patient_data)

    if result["prediction"] == 1:
        result["result"] = (
            "Higher-Diabetic-risk pattern estimated"
        )
    else:
        result["result"] = (
            "Lower-Diabetic-risk pattern estimated"
        )

    result["explanation"] = (
        explain_diabetes_prediction(
            patient_data
        )
    )

    try:
        save_prediction(
            user_id=user_id,
            disease="Diabetes",
            prediction=result["prediction"],
            result=result["result"],
            probability=result["probability"],
            input_data=json.dumps(patient_data),
            explanation=json.dumps(result["explanation"]),
            model_name=result["model"],
            model_version=result["model_version"],
        )

    except Exception as e:
        print(
            f"Database error while saving diabetes prediction: {e}"
        )

        raise HTTPException(
            status_code=500,
            detail="Could not save prediction."
        )

    return result

@app.post("/register")
def register_user(data: RegisterInput):
    existing_user = get_user_by_email(data.email)

    if existing_user:
        return {"error": "email already registered"}

    password_hash = pwd_context.hash(data.password)

    create_user(
        name=data.name,
        email=data.email,
        password_hash=password_hash,
    )

    return {"message": "User registered succesfully"}

@app.post("/login")
def login_user(data: LoginInput):
    user = get_user_by_email(data.email)

    if not user:
        return {"error": "Invalid email or password"}

    if not pwd_context.verify(data.password, user["password_hash"]):
        return {"error": "Invalid email or password"}

    token = create_access_token(
        user_id=user["id"],
        name=user["name"]
    )

    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    }

@app.get("/me")
def get_me(current_user_id: int = Depends(get_current_user)):

    user = get_user_by_id(current_user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return dict(user)

@app.put("/me")
def update_profile(
    data: UpdateProfileInput,
    user_id: int = Depends(get_current_user)
):
    try:
        # Check whether another user already has this email
        existing_user = email_exists_for_other_user(
            data.email.strip(),
            user_id
        )

        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Email is already registered to another account."
            )

        user = update_user(
            user_id=user_id,
            name=data.name.strip(),
            email=data.email.strip()
        )

        return dict(user)

    except HTTPException:
        raise

    except Exception as e:
        print(f"Database error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Could not update profile."
        )


@app.get("/history")
def get_history(user_id: int = Depends(get_current_user)):
    try:
        predictions = get_user_history(user_id)

        return [dict(prediction) for prediction in predictions]

    except Exception as e:
        print(f"Database error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve prediction history."
        )

@app.get("/history/{prediction_id}")
def get_prediction(
    prediction_id: int,
    user_id: int = Depends(get_current_user)
):
    try:
        prediction = get_prediction_by_id(
            prediction_id,
            user_id
        )

        if not prediction:
            raise HTTPException(
                status_code=404,
                detail="Prediction not found."
            )

        return dict(prediction)

    except HTTPException:
        raise

    except Exception as e:
        print(f"Database error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Could not retrieve prediction."
        )

@app.put("/change-password")
def change_password(
    data: ChangePasswordInput,
    user_id: int = Depends(get_current_user)
):
    try:
        user = get_user_by_id_with_password(user_id)

        if not user:
            raise HTTPException(
                status_code=404,
                detail="User not found."
            )

        # Verify current password
        if not pwd_context.verify(
            data.current_password,
            user["password_hash"]
        ):
            raise HTTPException(
                status_code=400,
                detail="Current password is incorrect."
            )

        # Prevent reusing the same password
        if pwd_context.verify(
            data.new_password,
            user["password_hash"]
        ):
            raise HTTPException(
                status_code=400,
                detail="New password must be different from your current password."
            )

        new_password_hash = pwd_context.hash(
            data.new_password
        )

        update_password(
            user_id=user_id,
            password_hash=new_password_hash
        )

        return {
            "message": "Password changed successfully."
        }

    except HTTPException:
        raise

    except Exception as e:
        print(f"Password change error: {e}")

        raise HTTPException(
            status_code=500,
            detail="Could not change password."
        )
