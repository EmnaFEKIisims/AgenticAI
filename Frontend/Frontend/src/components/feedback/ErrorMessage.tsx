interface ErrorMessageProps {
  message: string;
}

export default function ErrorMessage({ message }: ErrorMessageProps) {
  return <div className="planning-banner planning-banner-error">ERROR!! {message}</div>;
}
