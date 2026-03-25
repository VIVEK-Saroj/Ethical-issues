import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Camera, CheckCircle, Loader2, ImageIcon, MapPin } from 'lucide-react';
import api from '../api/client';
import Card from '../components/ui/Card';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';
import toast from 'react-hot-toast';
import type { ShelfImage } from '../types';

export default function UploadPage() {
  const [files, setFiles] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [storeId, setStoreId] = useState('store-1');
  const [aisle, setAisle] = useState('A1');
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<ShelfImage[]>([]);
  const [analyzing, setAnalyzing] = useState<Record<number, boolean>>({});

  const onDrop = useCallback((accepted: File[]) => {
    setFiles((prev) => [...prev, ...accepted]);
    const newPreviews = accepted.map((f) => URL.createObjectURL(f));
    setPreviews((prev) => [...prev, ...newPreviews]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.jpg', '.jpeg', '.png', '.webp'] },
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const removeFile = (index: number) => {
    URL.revokeObjectURL(previews[index]);
    setFiles((prev) => prev.filter((_, i) => i !== index));
    setPreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
    setUploading(true);
    try {
      const formData = new FormData();
      files.forEach((f) => formData.append('files', f));
      formData.append('store_id', storeId);
      formData.append('aisle', aisle);

      const { data } = await api.post<ShelfImage[]>('/images/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResults(data);
      toast.success(`${data.length} image(s) uploaded successfully!`);
      setFiles([]);
      setPreviews([]);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleAnalyze = async (imageId: number) => {
    setAnalyzing((prev) => ({ ...prev, [imageId]: true }));
    try {
      await api.post(`/images/${imageId}/analyze`);
      toast.success('Analysis complete!');
      // Refresh this result
      const { data } = await api.get(`/images/${imageId}`);
      setResults((prev) =>
        prev.map((r) => (r.id === imageId ? { ...r, ...data, processing_status: 'done' } : r))
      );
    } catch (err: any) {
      toast.error('Analysis failed');
    } finally {
      setAnalyzing((prev) => ({ ...prev, [imageId]: false }));
    }
  };

  const aisles = ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'D1', 'D2'];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Upload Shelf Scan</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
          Take photos of store shelves to analyze stock levels
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload area */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            {/* Store & Aisle selection */}
            <div className="flex flex-wrap gap-4 mb-6">
              <div className="flex-1 min-w-[150px]">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">
                  <MapPin size={14} className="inline mr-1" />Store
                </label>
                <select
                  value={storeId}
                  onChange={(e) => setStoreId(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none"
                >
                  <option value="store-1">Store #1 — Main Street</option>
                  <option value="store-2">Store #2 — Downtown</option>
                  <option value="store-3">Store #3 — Mall</option>
                </select>
              </div>
              <div className="flex-1 min-w-[150px]">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Aisle</label>
                <select
                  value={aisle}
                  onChange={(e) => setAisle(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none"
                >
                  {aisles.map((a) => (
                    <option key={a} value={a}>Aisle {a}</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Dropzone */}
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-200 ${
                isDragActive
                  ? 'border-brand-500 bg-brand-50 dark:bg-brand-950/20'
                  : 'border-gray-300 dark:border-gray-700 hover:border-brand-400 hover:bg-gray-50 dark:hover:bg-gray-900'
              }`}
            >
              <input {...getInputProps()} />
              <div className="flex flex-col items-center gap-3">
                <div className="w-14 h-14 rounded-2xl bg-brand-50 dark:bg-brand-950/30 flex items-center justify-center">
                  <Upload size={24} className="text-brand-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Drag & drop shelf photos, or <span className="text-brand-600">browse</span>
                  </p>
                  <p className="text-xs text-gray-400 mt-1">JPG, PNG, WebP — max 10MB each</p>
                </div>
                {/* Mobile camera button */}
                <div className="sm:hidden mt-2">
                  <label className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-600 text-white rounded-xl text-sm font-medium cursor-pointer">
                    <Camera size={16} />
                    Take Photo
                    <input
                      type="file"
                      accept="image/*"
                      capture="environment"
                      className="hidden"
                      onChange={(e) => {
                        const f = e.target.files;
                        if (f) onDrop(Array.from(f));
                      }}
                    />
                  </label>
                </div>
              </div>
            </div>

            {/* Previews */}
            {previews.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                  {files.length} file(s) selected
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                  {previews.map((src, i) => (
                    <div key={i} className="relative group rounded-xl overflow-hidden border border-gray-200 dark:border-gray-700">
                      <img src={src} alt={`Preview ${i + 1}`} className="w-full aspect-video object-cover" />
                      <button
                        onClick={() => removeFile(i)}
                        className="absolute top-1 right-1 w-6 h-6 bg-red-500 text-white rounded-full text-xs opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                      >
                        ×
                      </button>
                      <p className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-[10px] px-2 py-1 truncate">
                        {files[i]?.name}
                      </p>
                    </div>
                  ))}
                </div>

                <Button
                  onClick={handleUpload}
                  loading={uploading}
                  className="mt-4"
                  size="lg"
                >
                  <Upload size={16} className="mr-2" />
                  Upload & Process {files.length} Image(s)
                </Button>
              </div>
            )}
          </Card>
        </div>

        {/* Results sidebar */}
        <div className="space-y-4">
          <Card>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <ImageIcon size={16} />
              Upload Results
            </h3>
            {results.length === 0 ? (
              <div className="text-center py-8">
                <div className="w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center mx-auto mb-3">
                  <Camera size={20} className="text-gray-400" />
                </div>
                <p className="text-sm text-gray-500">No uploads yet</p>
                <p className="text-xs text-gray-400 mt-1">Upload shelf photos to start analysis</p>
              </div>
            ) : (
              <div className="space-y-3">
                {results.map((img) => (
                  <div key={img.id} className="p-3 rounded-xl border border-gray-100 dark:border-gray-800">
                    <div className="flex items-center justify-between mb-2">
                      <Badge variant={img.processing_status === 'done' ? 'success' : img.processing_status === 'pending' ? 'warning' : 'info'}>
                        {img.processing_status}
                      </Badge>
                      <span className="text-xs text-gray-400">#{img.id}</span>
                    </div>
                    <p className="text-xs text-gray-600 dark:text-gray-300">Aisle: {img.aisle}</p>
                    {img.processing_status === 'done' && (
                      <div className="mt-2 flex gap-2">
                        <Badge variant="info">{img.total_detections} items</Badge>
                        <Badge variant="success">{img.shelf_occupancy}%</Badge>
                      </div>
                    )}
                    {img.processing_status === 'pending' && (
                      <Button
                        size="sm"
                        className="mt-2 w-full"
                        onClick={() => handleAnalyze(img.id)}
                        loading={analyzing[img.id]}
                      >
                        {analyzing[img.id] ? 'Analyzing...' : 'Run Analysis'}
                      </Button>
                    )}
                    {img.processing_status === 'done' && (
                      <a
                        href={`/shelf-analysis?id=${img.id}`}
                        className="mt-2 block text-center text-xs text-brand-600 hover:underline"
                      >
                        View Details →
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
