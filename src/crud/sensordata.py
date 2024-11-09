from src.utils.commonImports import *
from src.models import model
from src.schemas import schemas
from src import crud

# Create sensor data entry
async def create_sensor_data(
    db: AsyncSession,
    sensor_data: schemas.SensorDataCreate
) -> None:  # Change the return type to None
    # Create a SensorData object and link it to the device
    new_sensor_data = model.SensorData(**sensor_data.dict())

    # Add and commit changes to the database
    db.add(new_sensor_data)
    await db.commit()
    await db.refresh(new_sensor_data)

# Get sensor data by its ID
async def get_sensor_data_by_id(db: AsyncSession, data_id: UUID) -> Optional[schemas.SensorDataWithRelations]:
    result = await db.execute(
        select(model.SensorData)
        .where(model.SensorData.data_id == data_id)
        .options(selectinload(model.SensorData.device))
    )
    sensor_data_record = result.scalar_one_or_none()

    if not sensor_data_record:
        return None

    # Convert to Pydantic model
    device_info = schemas.DeviceOut.model_validate(sensor_data_record.device.__dict__) if sensor_data_record.device else None
    
    return schemas.SensorDataWithRelations.model_validate({
        **sensor_data_record.__dict__,
        "device": device_info,
    })

# Get all sensor data recorded by a specific device
async def get_sensor_data_by_device_id(db: AsyncSession, device_id: UUID) -> List[schemas.SensorDataOut]:
    result = await db.execute(
        select(model.SensorData)
        .where(model.SensorData.device_id == device_id)
    )
    device_sensor_data = result.scalars().all()

    # Use model_validate for each entry
    return [schemas.SensorDataOut.model_validate(data) for data in device_sensor_data]

# Update sensor data by its ID
async def update_sensor_data(db: AsyncSession, data_id: UUID, sensor_data: schemas.SensorDataUpdate) -> Optional[schemas.SensorDataOut]:
    result = await db.execute(select(model.SensorData).where(model.SensorData.data_id == data_id))
    existing_sensor_data = result.scalar_one_or_none()
    
    if existing_sensor_data:
        # Update the fields based on the input data
        for key, value in sensor_data.dict(exclude_unset=True).items():
            setattr(existing_sensor_data, key, value)

        await db.commit()
        await db.refresh(existing_sensor_data)
        return schemas.SensorDataOut.model_validate(existing_sensor_data)
    
    return None

# Delete sensor data by its ID
async def delete_sensor_data(db: AsyncSession, data_id: UUID) -> bool:
    result = await db.execute(select(model.SensorData).where(model.SensorData.data_id == data_id))
    sensor_data_record = result.scalar_one_or_none()

    if sensor_data_record:
        # Delete the sensor data record
        await db.delete(sensor_data_record)
        await db.commit()
        return True

    return False
