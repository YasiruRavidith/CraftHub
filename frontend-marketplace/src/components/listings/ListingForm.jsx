// src/components/listings/ListingForm.jsx
import React, { useState, useEffect } from 'react';
import { useForm, Controller } from 'react-hook-form';
// import { useNavigate } from 'react-router-dom'; // Not used directly in this component
import Input from '../common/Input';
import Button from '../common/Button';
import Select from 'react-select'; // Assuming you'll install this: npm install react-select
import categoryService from '../../services/categoryService';

const RequiredIndicator = () => <span className="text-red-500 ml-1">*</span>;

const ListingForm = ({ onSubmitForm, initialData = {}, listingType = 'material', isLoading = false, apiFormError }) => {
  const { register, handleSubmit, control, watch, setValue, reset, formState: { errors, isDirty } } = useForm({
    defaultValues: initialData || {}, // Ensure initialData is an object
  });

  const [imagePreview, setImagePreview] = useState(initialData?.main_image_url || initialData?.thumbnail_image_url || null);
  const [categories, setCategories] = useState([]);
  const [categoryLoading, setCategoryLoading] = useState(false);

  useEffect(() => {
    // Reset form when initialData changes (e.g., for an edit form loading data)
    if (initialData && Object.keys(initialData).length > 0) {
      const currentImage = initialData.main_image_url || initialData.thumbnail_image_url;
      reset({
        ...initialData,
        category_id: initialData.category?.id || initialData.category_id || '', // Handle nested category or just id
      });
      setImagePreview(currentImage || null);
    } else {
      reset({}); // Reset to empty if no initial data (for create form)
      setImagePreview(null);
    }
  }, [initialData, reset]);


  useEffect(() => {
    const fetchCats = async () => {
      setCategoryLoading(true);
      try {
        const data = await categoryService.getCategories();
        setCategories(data.map(cat => ({ value: cat.id, label: cat.name })));
      } catch (error) {
        console.error("Failed to fetch categories", error);
        // Optionally set an error state to display to the user
      }
      setCategoryLoading(false);
    };
    fetchCats();
  }, []);

  const handleImageChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      // `main_image_file` is just a temporary name for react-hook-form to hold the File object
      // The actual field name sent to backend will be 'main_image' or 'thumbnail_image'
      setValue(listingType === 'material' ? 'main_image_file' : 'thumbnail_image_file', file, { shouldDirty: true });
      setImagePreview(URL.createObjectURL(file));
    } else {
      // If file selection is cancelled or cleared
      setValue(listingType === 'material' ? 'main_image_file' : 'thumbnail_image_file', null, { shouldDirty: true });
      setImagePreview(initialData?.main_image_url || initialData?.thumbnail_image_url || null); // Revert to initial or null
    }
  };

  const internalOnSubmit = (data) => {
    const formData = new FormData();

    const imageFileKey = listingType === 'material' ? 'main_image_file' : 'thumbnail_image_file';
    const backendImageKey = listingType === 'material' ? 'main_image' : 'thumbnail_image';

    if (data[imageFileKey] instanceof File) {
      formData.append(backendImageKey, data[imageFileKey], data[imageFileKey].name);
    }

    Object.keys(data).forEach(key => {
      if (key === imageFileKey) return; // Already handled

      // Convert empty strings for number fields to null or omit them
      // so backend doesn't try to parse "" as integer.
      const modelField = initialData?._modelFields?.[key]; // Hypothetical: if you pass model field types
      const value = data[key];

      if (
        (key === 'stock_quantity' || key === 'weight_gsm' || key === 'width_cm' || key === 'lead_time_days') &&
        (value === '' || value === null || value === undefined)
      ) {
        // Omit if empty and optional (null=True on backend model)
        // If backend requires null for empty optional integers, send null.
        // For now, we omit. If your serializer expects null, then append null.
        return; 
      }
      
      if (key === 'category_id' && value && typeof value === 'object') {
        formData.append(key, value.value); // For react-select, value is { value: 'id', label: 'name' }
      } else if (value !== null && value !== undefined) {
        formData.append(key, value);
      }
    });
    
    // seller_id or designer_id should be set by the backend based on request.user
    // So, we don't explicitly add it here for CREATE operations.
    // For UPDATE operations, it would already be part of initialData and thus in 'data'.

    onSubmitForm(formData);
  };

  const isMaterial = listingType === 'material';
  // const isDesign = listingType === 'design'; // Not used below, but good for clarity

  const materialUnitOptions = [
    { value: 'm', label: 'Meter (m)' }, { value: 'kg', label: 'Kilogram (kg)' },
    { value: 'sqm', label: 'Square Meter (sqm)' }, { value: 'pcs', label: 'Pieces (pcs)' },
    { value: 'yard', label: 'Yard (yd)' }, { value: 'lb', label: 'Pound (lb)' },
  ];

  return (
    <form onSubmit={handleSubmit(internalOnSubmit)} className="space-y-6">
      {apiFormError && <p className="text-sm text-red-600 bg-red-100 p-3 rounded-md">{apiFormError}</p>}

      <Input
        label={<>{isMaterial ? "Material Name" : "Design Title"} <RequiredIndicator /></>}
        id={isMaterial ? "name" : "title"}
        {...register(isMaterial ? "name" : "title", { required: "This field is required" })}
        error={errors[isMaterial ? "name" : "title"]}
      />

      <div>
        <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
          Description <RequiredIndicator />
        </label>
        <textarea
          id="description"
          rows="4"
          {...register("description", { required: "Description is required" })}
          className={`mt-1 block w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm ${errors.description ? 'border-red-500' : ''}`}
        />
        {errors.description && <p className="mt-1 text-xs text-red-600">{errors.description.message}</p>}
      </div>
      
      <div>
        <label htmlFor="category_id" className="block text-sm font-medium text-gray-700 mb-1">
            Category <RequiredIndicator />
        </label>
        <Controller
            name="category_id"
            control={control}
            rules={{ required: "Category is required" }}
            render={({ field }) => (
              <Select
                {...field}
                options={categories}
                isLoading={categoryLoading}
                placeholder="Select a category..."
                classNamePrefix="react-select" // For styling if you add custom react-select styles
                className={`mt-1 react-select-container ${errors.category_id ? 'react-select-error' : ''}`}
                inputId="category_id"
              />
            )}
        />
        {errors.category_id && <p className="mt-1 text-xs text-red-600">{errors.category_id.message}</p>}
      </div>

      <div>
        <label htmlFor="main_image_input" className="block text-sm font-medium text-gray-700 mb-1">
          {isMaterial ? "Main Material Image" : "Thumbnail Image"} (Optional)
        </label>
        {imagePreview && <img src={imagePreview} alt="Preview" className="w-40 h-40 object-cover mb-2 rounded-md border" />}
        <input
          type="file"
          id="main_image_input"
          accept="image/*"
          {...register(isMaterial ? 'main_image_file' : 'thumbnail_image_file')} // Use RHF register
          onChange={handleImageChange} // Still useful if you want immediate side-effects not tied to RHF's own onChange
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />
        {/* Add error display for image if needed, RHF can validate file types/size with custom rules */}
      </div>

      {isMaterial && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input
              label={<>Price Per Unit <RequiredIndicator /></>}
              id="price_per_unit"
              type="number"
              step="0.01"
              {...register("price_per_unit", { required: "Price is required", valueAsNumber: true, min: {value: 0.01, message: "Price must be greater than 0"} })}
              error={errors.price_per_unit}
            />
            <div>
                <label htmlFor="unit" className="block text-sm font-medium text-gray-700 mb-1">Unit <RequiredIndicator /></label>
                <select
                  id="unit"
                  {...register("unit", { required: "Unit is required" })}
                  className={`mt-1 block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md ${errors.unit ? 'border-red-500' : ''}`}
                  defaultValue="m"
                >
                  {materialUnitOptions.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                </select>
                {errors.unit && <p className="mt-1 text-xs text-red-600">{errors.unit.message}</p>}
            </div>
          </div>
          <Input
            label={<>Minimum Order Quantity (MOQ) <RequiredIndicator /></>}
            id="minimum_order_quantity"
            type="number"
            step="1"
            {...register("minimum_order_quantity", { required: "MOQ is required", valueAsNumber: true, min: {value: 1, message:"MOQ must be at least 1"} })}
            error={errors.minimum_order_quantity}
            defaultValue={1}
          />
          <Input
            label="Stock Quantity (Optional)"
            id="stock_quantity"
            type="number"
            step="1"
            {...register("stock_quantity", { 
                valueAsNumber: true, 
                min: {value: 0, message: "Stock can't be negative"},
                validate: value => !isNaN(value) || value === null || value === '' || 'Must be a number' // Allow empty string to be omitted
            })}
            error={errors.stock_quantity}
          />
          <Input label="SKU (Optional)" id="sku" {...register("sku")} error={errors.sku} />
          <Input label="Composition (e.g., 100% Cotton) (Optional)" id="composition" {...register("composition")} error={errors.composition} />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Input label="Weight (GSM, Optional)" id="weight_gsm" type="number" {...register("weight_gsm", {valueAsNumber:true, min:0, validate: value => !isNaN(value) || value === null || value === '' || 'Must be a number'})} error={errors.weight_gsm} />
            <Input label="Width (cm, Optional)" id="width_cm" type="number" {...register("width_cm", {valueAsNumber:true, min:0, validate: value => !isNaN(value) || value === null || value === '' || 'Must be a number'})} error={errors.width_cm} />
          </div>
          <Input label="Country of Origin (Optional)" id="country_of_origin" {...register("country_of_origin")} error={errors.country_of_origin} />
          <Input label="Lead Time (days, Optional)" id="lead_time_days" type="number" {...register("lead_time_days", {valueAsNumber:true, min:0, validate: value => !isNaN(value) || value === null || value === '' || 'Must be a number'})} error={errors.lead_time_days} />
        </>
      )}

      {/* Design specific fields would go here, similar structure */}
      {/* ... */}
      
      <div className="pt-4">
        <Button type="submit" variant="primary" className="w-full md:w-auto" isLoading={isLoading} disabled={isLoading || (!isDirty && !!initialData?.id)}>
          {isLoading ? 'Saving...' : (initialData?.id ? 'Save Changes' : 'Create Listing')}
        </Button>
      </div>
    </form>
  );
};

export default ListingForm;