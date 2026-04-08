import { useEffect, useState } from 'react';
import { Camera, Search, Filter, Eye, BarChart3, Layers, EyeOff } from 'lucide-react';
import api, { mediaUrl } from '../api/client';
import Card from '../components/ui/Card';
import Badge from '../components/ui/Badge';
import Modal from '../components/ui/Modal';
import Spinner from '../components/ui/Spinner';
import type { ShelfImage, ImageWithDetections, Detection } from '../types';

export default function ShelfAnalysisPage() {
  const [images, setImages] = useState<ShelfImage[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState<ImageWithDetections | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);
  const [filter, setFilter] = useState('');
  const [imgDims, setImgDims] = useState<{ w: number; h: number }>({ w: 800, h: 600 });
  const [showBoxes, setShowBoxes] = useState(true);
  const [hoveredDet, setHoveredDet] = useState<number | null>(null);

  useEffect(() => {
    api.get('/images/')
      .then(({ data }) => setImages(data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const openDetail = async (id: number) => {
    setDetailLoading(true);
    setModalOpen(true);
    setImgDims({ w: 800, h: 600 }); // reset until actual image loads
    try {
      const { data } = await api.get<ImageWithDetections>(`/images/${id}`);
      setSelectedImage(data);
    } catch {
      setSelectedImage(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const filtered = images.filter(
    (img) =>
      img.aisle.toLowerCase().includes(filter.toLowerCase()) ||
      img.processing_status.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Shelf Analysis</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            Review shelf scans and detection results
          </p>
        </div>
        <div className="relative w-full sm:w-64">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search by aisle..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-900 text-sm text-gray-900 dark:text-white focus:ring-2 focus:ring-brand-500 outline-none"
          />
        </div>
      </div>

      {loading ? (
        <div className="flex justify-center py-20"><Spinner size="lg" /></div>
      ) : filtered.length === 0 ? (
        <Card className="text-center py-16">
          <Camera size={48} className="text-gray-300 dark:text-gray-700 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-1">No shelf scans found</h3>
          <p className="text-sm text-gray-500">Upload shelf photos to see analysis results here</p>
          <a href="/upload" className="inline-block mt-4 text-sm text-brand-600 hover:underline">Go to Upload →</a>
        </Card>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {filtered.map((img) => (
            <Card key={img.id} padding={false} hover className="overflow-hidden cursor-pointer" onClick={() => openDetail(img.id)}>
              <div className="aspect-video bg-gray-100 dark:bg-gray-800 relative overflow-hidden">
                <img
                  src={mediaUrl(img.image_url)}
                  alt={`Aisle ${img.aisle}`}
                  className="w-full h-full object-cover hover:scale-105 transition-transform duration-300"
                  loading="lazy"
                  referrerPolicy="no-referrer"
                  crossOrigin="anonymous"
                />
                <div className="absolute top-2 left-2">
                  <Badge
                    variant={
                      img.processing_status === 'done'
                        ? 'success'
                        : img.processing_status === 'failed'
                        ? 'danger'
                        : 'warning'
                    }
                  >
                    {img.processing_status}
                  </Badge>
                </div>
                <div className="absolute top-2 right-2">
                  <Badge variant="info">{img.aisle}</Badge>
                </div>
              </div>
              <div className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">Aisle {img.aisle}</p>
                  <Eye size={14} className="text-gray-400" />
                </div>
                <div className="flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                  <span className="flex items-center gap-1">
                    <BarChart3 size={12} />
                    {img.total_detections} items
                  </span>
                  <span>{img.shelf_occupancy}% full</span>
                </div>
                <p className="text-[10px] text-gray-400 mt-2">
                  {new Date(img.upload_timestamp).toLocaleString()}
                </p>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Detail Modal */}
      <Modal open={modalOpen} onClose={() => setModalOpen(false)} title="Shelf Scan Detail" size="xl">
        {detailLoading ? (
          <div className="flex justify-center py-12"><Spinner /></div>
        ) : selectedImage ? (
          <div className="space-y-4">
            {/* Toolbar */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Badge variant="info">{selectedImage.aisle}</Badge>
                <Badge variant="success">{selectedImage.total_detections} detections</Badge>
                <Badge variant="warning">{selectedImage.shelf_occupancy}% occupancy</Badge>
              </div>
              <button
                onClick={() => setShowBoxes(!showBoxes)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
              >
                {showBoxes ? <EyeOff size={14} /> : <Layers size={14} />}
                {showBoxes ? 'Hide Boxes' : 'Show Boxes'}
              </button>
            </div>

            {/* Annotated image with bounding box overlays */}
            <div className="relative rounded-xl overflow-hidden bg-gray-100 dark:bg-gray-800">
              <img
                src={mediaUrl(selectedImage.image_url)}
                alt={`Aisle ${selectedImage.aisle}`}
                className="w-full block"
                referrerPolicy="no-referrer"
                crossOrigin="anonymous"
                onLoad={(e) => {
                  const img = e.currentTarget;
                  if (img.naturalWidth && img.naturalHeight) {
                    setImgDims({ w: img.naturalWidth, h: img.naturalHeight });
                  }
                }}
              />
              {/* Bounding box overlays */}
              {showBoxes && (
                <svg
                  className="absolute inset-0 w-full h-full pointer-events-none"
                  viewBox={`0 0 ${imgDims.w} ${imgDims.h}`}
                  preserveAspectRatio="xMidYMid meet"
                >
                  {selectedImage.detections.map((det, i) => {
                    const color = det.confidence > 0.7 ? '#10b981' : det.confidence > 0.4 ? '#f59e0b' : '#ef4444';
                    const isHovered = hoveredDet === i;
                    const sw = Math.max(imgDims.w, imgDims.h) * 0.002;
                    return (
                      <g key={i} style={{ pointerEvents: 'all' }}
                        onMouseEnter={() => setHoveredDet(i)}
                        onMouseLeave={() => setHoveredDet(null)}
                      >
                        <rect
                          x={det.bounding_box.x1}
                          y={det.bounding_box.y1}
                          width={det.bounding_box.x2 - det.bounding_box.x1}
                          height={det.bounding_box.y2 - det.bounding_box.y1}
                          fill={isHovered ? `${color}33` : 'none'}
                          stroke={color}
                          strokeWidth={isHovered ? sw * 2.5 : sw}
                          rx={sw}
                          opacity={isHovered ? 1 : 0.7}
                        />
                        {/* Only show label on hover */}
                        {isHovered && (() => {
                          const label = `${det.product_name || det.class_label} ${(det.confidence * 100).toFixed(0)}%`;
                          const fs = Math.max(imgDims.w, imgDims.h) * 0.014;
                          const lh = fs + fs * 0.5;
                          const lw = label.length * fs * 0.6 + fs;
                          return (
                            <>
                              <rect
                                x={det.bounding_box.x1}
                                y={det.bounding_box.y1 - lh - sw}
                                width={lw}
                                height={lh}
                                fill={color}
                                rx={sw}
                              />
                              <text
                                x={det.bounding_box.x1 + fs * 0.3}
                                y={det.bounding_box.y1 - sw - fs * 0.25}
                                fill="white"
                                fontSize={fs}
                                fontWeight="bold"
                                fontFamily="system-ui, sans-serif"
                              >
                                {label}
                              </text>
                            </>
                          );
                        })()}
                      </g>
                    );
                  })}
                </svg>
              )}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-950/20 text-center">
                <p className="text-2xl font-bold text-blue-600">{selectedImage.total_detections}</p>
                <p className="text-xs text-blue-500">Items Detected</p>
              </div>
              <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-950/20 text-center">
                <p className="text-2xl font-bold text-emerald-600">{selectedImage.shelf_occupancy}%</p>
                <p className="text-xs text-emerald-500">Shelf Occupancy</p>
              </div>
              <div className="p-3 rounded-xl bg-violet-50 dark:bg-violet-950/20 text-center">
                <p className="text-2xl font-bold text-violet-600">
                  {new Set(selectedImage.detections.map(d => d.product_name).filter(Boolean)).size}
                </p>
                <p className="text-xs text-violet-500">Products Matched</p>
              </div>
            </div>

            {/* Detections table */}
            <div className="max-h-60 overflow-y-auto">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-white dark:bg-gray-900">
                  <tr className="border-b border-gray-100 dark:border-gray-800">
                    <th className="text-left py-2 font-medium text-gray-500 text-xs">#</th>
                    <th className="text-left py-2 font-medium text-gray-500 text-xs">Detected Object</th>
                    <th className="text-left py-2 font-medium text-gray-500 text-xs">Linked Product</th>
                    <th className="text-left py-2 font-medium text-gray-500 text-xs">Position</th>
                    <th className="text-right py-2 font-medium text-gray-500 text-xs">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedImage.detections.map((det, i) => (
                    <tr
                      key={i}
                      className={`border-b border-gray-50 dark:border-gray-800/50 cursor-pointer transition-colors ${hoveredDet === i ? 'bg-brand-50 dark:bg-brand-950/20' : 'hover:bg-gray-50 dark:hover:bg-gray-800/50'}`}
                      onMouseEnter={() => setHoveredDet(i)}
                      onMouseLeave={() => setHoveredDet(null)}
                    >
                      <td className="py-2 text-xs text-gray-400">{i + 1}</td>
                      <td className="py-2 font-medium text-gray-900 dark:text-white capitalize">{det.class_label}</td>
                      <td className="py-2 text-gray-600 dark:text-gray-400 text-xs">
                        {det.product_name ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-brand-50 dark:bg-brand-950/20 text-brand-700 dark:text-brand-300 rounded-full">
                            {det.product_name}
                          </span>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td className="py-2 text-gray-500 capitalize text-xs">{det.position_on_shelf || '—'}</td>
                      <td className="py-2 text-right">
                        <Badge variant={det.confidence > 0.7 ? 'success' : det.confidence > 0.5 ? 'warning' : 'danger'}>
                          {(det.confidence * 100).toFixed(0)}%
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <p className="text-center text-gray-400 py-8">Could not load details</p>
        )}
      </Modal>
    </div>
  );
}
