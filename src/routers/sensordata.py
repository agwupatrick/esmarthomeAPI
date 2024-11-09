from src.utils.commonImports import *
from src.utils.commonSession import get_session
from src.crud.users import get_current_active_user
from src.schemas import schemas
from src.models import model
from src import crud

router = APIRouter(prefix="/sensor", tags=["Sensor Data"])

# Create sensor data entry endpoint
@router.post("/", status_code=status.HTTP_201_CREATED)  # Set default status code to 201
async def create_sensor_data_endpoint(
    sensor_data: schemas.SensorDataCreate,
    db: AsyncSession = Depends(get_session)
):
    # Ensure the current user has permission to add sensor data (authorization logic may be added here)
    try:
        await crud.sensordata.create_sensor_data(db, sensor_data)
        return Response(status_code=status.HTTP_201_CREATED)  # Return empty response with 201 status
    except Exception as e:
        # Handle any exceptions and return a 400 status code if needed
        raise HTTPException(status_code=400, detail=str(e))
    

# Get sensor data by ID, including device information
@router.get("/{data_id}", response_model=schemas.SensorDataWithRelations)
async def get_sensor_data_by_id_endpoint(
    data_id: UUID,
    db: AsyncSession = Depends(get_session)
):
    sensor_data = await crud.sensordata.get_sensor_data_by_id(db, data_id=data_id)

    if not sensor_data:
        raise HTTPException(status_code=404, detail="Sensor data not found")

    return sensor_data

# Get all sensor data recorded by a specific device
@router.get("/by-device/{device_id}", response_model=List[schemas.SensorDataOut])
async def get_sensor_data_by_device_id_endpoint(
    device_id: UUID,
    db: AsyncSession = Depends(get_session)
):
    sensor_data_list = await crud.sensordata.get_sensor_data_by_device_id(db, device_id=device_id)

    if not sensor_data_list:
        raise HTTPException(status_code=404, detail="No sensor data found for this device")

    return sensor_data_list

# Update sensor data by ID
@router.put("/{data_id}", response_model=schemas.SensorDataOut)
async def update_sensor_data_endpoint(
    data_id: UUID,
    sensor_data: schemas.SensorDataUpdate,
    db: AsyncSession = Depends(get_session),
    current_user: schemas.UserOut = Depends(get_current_active_user)
):
    # Fetch the sensor data to ensure it exists
    existing_sensor_data = await crud.sensordata.get_sensor_data_by_id(db, data_id=data_id)
    if not existing_sensor_data:
        raise HTTPException(status_code=404, detail="Sensor data not found")

    # Authorization: Ensure the user has permission to update
    if existing_sensor_data.device_id != current_user.device_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this sensor data")

    updated_sensor_data = await crud.sensordata.update_sensor_data(db, data_id=data_id, sensor_data=sensor_data)

    if not updated_sensor_data:
        raise HTTPException(status_code=404, detail="Failed to update sensor data")

    return updated_sensor_data

# Delete sensor data by ID
@router.delete("/{data_id}", status_code=204)
async def delete_sensor_data_endpoint(
    data_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: schemas.UserOut = Depends(get_current_active_user)
):
    # Fetch the sensor data to ensure it exists and the user has permission to delete
    sensor_data = await crud.sensordata.get_sensor_data_by_id(db, data_id=data_id)

    if not sensor_data:
        raise HTTPException(status_code=404, detail="Sensor data not found")

    # Authorization: Ensure the current user is associated with the device
    if sensor_data.device_id != current_user.device_id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this sensor data")

    deleted = await crud.sensordata.delete_sensor_data(db, data_id=data_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Failed to delete sensor data")

    return {"message": "Sensor data deleted successfully"}
