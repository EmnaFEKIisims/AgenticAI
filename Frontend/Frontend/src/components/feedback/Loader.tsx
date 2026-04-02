interface LoaderProps {
  message?: string;
}

export default function Loader({ message = "Generating schedule..." }: LoaderProps) {
  return <div className="planning-banner planning-banner-info">{message}</div>;
}
